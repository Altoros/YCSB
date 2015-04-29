package com.yahoo.ycsb.couchbase;

import com.couchbase.client.java.Bucket;
import com.couchbase.client.java.Cluster;
import com.couchbase.client.java.CouchbaseCluster;
import com.couchbase.client.java.document.JsonDocument;
import com.couchbase.client.java.document.json.JsonObject;
import com.couchbase.client.java.error.CASMismatchException;
import com.yahoo.ycsb.ByteIterator;
import com.yahoo.ycsb.DBException;
import com.yahoo.ycsb.StringByteIterator;
import com.yahoo.ycsb.memcached.MemcachedCompatibleClient;
import net.spy.memcached.MemcachedClient;
import com.couchbase.client.java.PersistTo;
import com.couchbase.client.java.ReplicateTo;

import rx.Observable;
import rx.functions.Action1;
import rx.functions.Func0;
import rx.functions.Func1;

import java.util.*;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * This client uses Couchbase Java SDK 2.1.1 and supports Couchbase Server 3.0
 */
public class CouchbaseClient extends MemcachedCompatibleClient {

    private static CouchbaseConfig config;

    private PersistTo persistTo;
    private ReplicateTo replicateTo;
    private Bucket defaultBucket;

    private Map<String, Integer> docUpdateRaces = new HashMap<>();

    private static class ClusterHolder {
        public static final Cluster CLUSTER = CouchbaseCluster.create(config.getHosts());
    }

    private static Cluster getClusterInstance() {
        return ClusterHolder.CLUSTER;
    }

    private static class BucketHolder {
        public static final Bucket BUCKET = getClusterInstance().openBucket(config.getBucket());
    }

    private static Bucket getBucketInstance() {
        return BucketHolder.BUCKET;
    }

    @Override
    protected MemcachedClient createMemcachedClient() throws Exception {
        return null;
    }

    @Override
    public void init() throws DBException {
        try {
            config = new CouchbaseConfig(getProperties());
            persistTo = config.getPersistTo();
            replicateTo = config.getReplicateTo();

            // Open the default bucket
            defaultBucket = getBucketInstance();
        } catch (Exception e) {
            throw new DBException(e);
        }
    }

    @Override
    public int read(String table, String key, Set<String> fields, Map<String, ByteIterator> result) {
        try {
            JsonDocument doc = defaultBucket.get(createQualifiedKey(table, key));

            if (doc == null)
                return ERROR;

            for (String field : doc.content().getNames())
                result.put(field, new StringByteIterator(doc.content().getString(field)));

            return OK;
        }
        catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
    }

    @Override
    public int updateOne(String table, String key, String field, ByteIterator value) {
        return update(table, key, Collections.singletonMap(field, value));
    }

    @Override
    public int updateAll(String table, String key, Map<String, ByteIterator> values) {
        return update(table, key, values);
    }

    @Override
    public int update(String table, String key, Map<String, ByteIterator> values) {
        switch (config.getUpdateType()) {
            case SYNC_CAS_LOOP:   return doSyncUpdateWithCasLoop(table, key, values);
            case ASYNC_CAS_LOOP:  return doAsyncUpdateWithCasLoop(table, key, values);
            case SYNC_LOCAL_LOCK: return doSyncUpdateWithLocalLock(table, key, values);
            default: throw new IllegalArgumentException("Unknown " + config.getUpdateType() + " update type");
        }
    }

    public int doSyncUpdateWithLocalLock(String table, String key, Map<String, ByteIterator> values) {
        synchronized (key.intern()) {
            String qualifiedKey = createQualifiedKey(table, key);

            JsonDocument doc = defaultBucket.get(qualifiedKey);
            if (doc == null)
                return ERROR;

            for (Map.Entry<String, ByteIterator> field : values.entrySet())
                doc.content().put(field.getKey(), field.getValue().toString());

            try {
                defaultBucket.upsert(doc, persistTo, replicateTo);
                return OK;
            }
            catch (Exception e) {
                e.printStackTrace();
                return ERROR;
            }
        }
    }

    public int doSyncUpdateWithCasLoop(String table, String key, Map<String, ByteIterator> values) {
        String qualifiedKey = createQualifiedKey(table, key);

        while (true) {
            JsonDocument doc = defaultBucket.get(qualifiedKey);
            if (doc == null)
                return ERROR;

            for (Map.Entry<String, ByteIterator> field : values.entrySet())
                doc.content().put(field.getKey(), field.getValue().toString());

            try {
                defaultBucket.replace(doc, persistTo, replicateTo);
                return OK;
            }
            catch (CASMismatchException ce) {
                incDocUpdateRace(key);
                sleep(config.getConcurrentUpdateRetryTimeMillis());
            }
            catch (Exception e) {
                e.printStackTrace();
                return ERROR;
            }
        }
    }

    private int doAsyncUpdateWithCasLoop(String table, String key, final Map<String, ByteIterator> values) {
        final CountDownLatch latch = new CountDownLatch(1);

        Observable.defer(getDocFunc(createQualifiedKey(table, key)))
                  .map(updateDocFieldsFunc(values))
                  .flatMap(replaceDocFunc())
                  .retryWhen(retryPolicyFunc())
                  .subscribe(new Action1<Object>() {
                      @Override
                      public void call(Object jsonDocument) {
                          latch.countDown();
                      }
                  });

        try {
            latch.await();
            return OK;
        } catch (InterruptedException e) {
            e.printStackTrace();
            return ERROR;
        }
    }

    private Func0<Observable<JsonDocument>> getDocFunc(final String key) {
        return new Func0<Observable<JsonDocument>>() {
            @Override
            public Observable<JsonDocument> call() {
                return defaultBucket.async().get(key);
            }
        };
    }

    private Func1<JsonDocument, Observable<?>> replaceDocFunc() {
        return new Func1<JsonDocument, Observable<?>>() {
            @Override
            public Observable<?> call(JsonDocument doc) {
                return defaultBucket.async().replace(doc);
            }
        };
    }

    private Func1<JsonDocument, JsonDocument> updateDocFieldsFunc(final Map<String, ByteIterator> values) {
        return new Func1<JsonDocument, JsonDocument>() {
            @Override
            public JsonDocument call(JsonDocument doc) {
                for (Map.Entry<String, ByteIterator> field : values.entrySet())
                    doc.content().put(field.getKey(), field.getValue().toString());
                return doc;
            }
        };
    }

    private Func1<Observable<? extends Throwable>, Observable<?>> retryPolicyFunc() {
        return new Func1<Observable<? extends Throwable>, Observable<?>>() {
            @Override
            public Observable<?> call(Observable<? extends Throwable> attempts) {
                return attempts.flatMap(new Func1<Throwable, Observable<?>>() {
                    @Override
                    public Observable<?> call(Throwable e) {
                        if (e instanceof CASMismatchException)
                            return Observable.timer(config.getConcurrentUpdateRetryTimeMillis(), TimeUnit.MILLISECONDS);
                        else
                            return Observable.error(e);
                    }
                });
            }
        };
    }

    @Override
    public int insert(String table, String key, Map<String, ByteIterator> values) {
        JsonObject record = JsonObject.empty();
        for (String field : values.keySet())
            record.put(field, values.get(field).toString());

        JsonDocument document = JsonDocument.create(createQualifiedKey(table, key), objectExpirationTime, record);
        try {
            defaultBucket.insert(document, persistTo, replicateTo);
            return OK;
        }
        catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
    }

    @Override
    public int delete(String table, String key) {
        try {
            defaultBucket.remove(createQualifiedKey(table, key), persistTo, replicateTo);
            return OK;
        }
        catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
    }

    @Override
    public void cleanup() throws DBException {
        super.cleanup();
        printDocUpdateRacesStatistics();
    }

    private void printDocUpdateRacesStatistics() {
        StringBuilder buf = new StringBuilder();

        for (Map.Entry<String, Integer> docKey : docUpdateRaces.entrySet()) {
            buf.append(keyUpdateRacesToString(docKey));
            buf.append('\n');
        }

        System.out.println(buf.toString());
    }

    private String keyUpdateRacesToString(Map.Entry<String, Integer> keyRaces) {
        return keyRaces.getKey() + " : " + keyRaces.getValue();
    }

    private void incDocUpdateRace(String key) {
        Integer races = docUpdateRaces.get(key);
        if (races == null)
            docUpdateRaces.put(key, 1);
        else
            docUpdateRaces.put(key, races + 1);
    }

    private void sleep(long ms) {
        try {
            Thread.sleep(ms);
        }
        catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
