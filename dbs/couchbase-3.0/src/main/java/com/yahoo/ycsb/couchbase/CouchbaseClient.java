package com.yahoo.ycsb.couchbase;

import com.couchbase.client.java.Bucket;
import com.couchbase.client.java.Cluster;
import com.couchbase.client.java.CouchbaseCluster;
import com.couchbase.client.java.document.JsonDocument;
import com.couchbase.client.java.document.json.JsonObject;
import com.couchbase.client.java.error.CASMismatchException;
import com.couchbase.client.java.error.DocumentDoesNotExistException;
import com.yahoo.ycsb.ByteIterator;
import com.yahoo.ycsb.DBException;
import com.yahoo.ycsb.StringByteIterator;
import com.yahoo.ycsb.memcached.MemcachedCompatibleClient;
import net.spy.memcached.MemcachedClient;
import com.couchbase.client.java.PersistTo;
import com.couchbase.client.java.ReplicateTo;
import rx.Observable;
import rx.functions.Func0;
import rx.functions.Func1;

import java.util.Collections;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * This client uses Couchbase Java SDK 2.1.1 and supports Couchbase Server 3.0
 */
public class CouchbaseClient extends MemcachedCompatibleClient {

    protected static CouchbaseConfig config;

    protected PersistTo persistTo;
    protected ReplicateTo replicateTo;
    protected Bucket defaultBucket;
    protected Cluster cluster;

    protected CouchbaseConfig createMemcachedConfig() {
        return new CouchbaseConfig(getProperties());
    }

    @Override
    protected MemcachedClient createMemcachedClient() throws Exception {
        return null;
    }

    public static class ClusterHolder {
        public static final Cluster CLUSTER = CouchbaseCluster.create(config.getHosts());
    }

    public static Cluster getClusterInstance() {
        return ClusterHolder.CLUSTER;
    }

    public static class BucketHolder {
        public static final Bucket BUCKET = getClusterInstance().openBucket();
    }

    public static Bucket getBucketInstance() {
        return BucketHolder.BUCKET;
    }

    @Override
    public void init() throws DBException {
        try {
            config = createMemcachedConfig();
            persistTo = config.getPersistTo();
            replicateTo = config.getReplicateTo();

            // Connect to cluster
            cluster = getClusterInstance();

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
        key = createQualifiedKey(table, key);
        try {
            final Iterator<Map.Entry<String, ByteIterator>> entries = values.entrySet().iterator();
            final String keyCopy = key;
            Observable.defer(new Func0<Observable<JsonDocument>>() {
                @Override
                public Observable<JsonDocument> call() {
                    return defaultBucket.async().get(keyCopy);
                }
            }).map(new Func1<JsonDocument, JsonDocument>() {
                @Override
                public JsonDocument call(JsonDocument document) {
                    if (document == null) {
                        System.err.println("Document not found!");
                        throw new DocumentDoesNotExistException();
                    }
                    while (entries.hasNext()) {
                        final Map.Entry<String, ByteIterator> entry = entries.next();
                        document.content().put(entry.getKey(), entry.getValue().toString());
                    }
                    return document;
                }
            }).flatMap(new Func1<JsonDocument, Observable<JsonDocument>>() {
                @Override
                public Observable<JsonDocument> call(JsonDocument document) {
                    return defaultBucket.async().replace(document, persistTo, replicateTo);
                }
            }).retryWhen(new Func1<Observable<? extends Throwable>, Observable<Long>>() {
                @Override
                public Observable<Long> call(Observable<? extends Throwable> attempts) {
                    return attempts.flatMap(new Func1<Throwable, Observable<Long>>() {
                        @Override
                        public Observable<Long> call(Throwable e) {
                            if (!(e instanceof CASMismatchException)) {
                                return Observable.error(e);
                            }
                            System.out.println("Retry update");
                            return Observable.timer(50, TimeUnit.MILLISECONDS);
                        }
                    });
                }
            }).subscribe();

        } catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
        return OK;
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
}
