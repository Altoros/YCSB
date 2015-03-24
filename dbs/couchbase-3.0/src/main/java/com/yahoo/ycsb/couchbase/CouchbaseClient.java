package com.yahoo.ycsb.couchbase;

import com.couchbase.client.java.Bucket;
import com.couchbase.client.java.Cluster;
import com.couchbase.client.java.CouchbaseCluster;
import com.couchbase.client.java.document.JsonDocument;
import com.couchbase.client.java.document.json.JsonObject;
import com.couchbase.client.java.error.CASMismatchException;
import com.yahoo.ycsb.ByteIterator;
import com.yahoo.ycsb.DBException;
import com.yahoo.ycsb.memcached.MemcachedCompatibleClient;
import net.spy.memcached.MemcachedClient;
import net.spy.memcached.PersistTo;
import net.spy.memcached.ReplicateTo;
import rx.Observable;
import rx.functions.Action1;
import rx.functions.Func0;
import rx.functions.Func1;

import java.util.Collections;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/**
 * Alexei Okhrimenko, 2015
 *
 * this client uses Couchbase Java SDK 2.1.1 and supports Couchbase Server 3.0
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
        key = createQualifiedKey(table, key);
        try {
            defaultBucket.get(key);
            return OK;
        } catch (Exception e) {
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
            Iterator<Map.Entry<String, ByteIterator>> entries = values.entrySet().iterator();
            while (entries.hasNext()) {
                final Map.Entry<String, ByteIterator> entry = entries.next();
                Observable<JsonDocument> loaded = defaultBucket.async().get(key);
                if (loaded == null) {
                    System.err.println("Document not found!");
                } else {
                    final String finalKey = key;
                    Observable.defer(new Func0<Observable<JsonDocument>>() {
                        @Override
                        public Observable<JsonDocument> call() {
                            return defaultBucket.async().get(finalKey);
                        }
                    })
                            .map(new Func1<JsonDocument, JsonDocument>() {
                                @Override
                                public JsonDocument call(JsonDocument document) {
                                    document.content().put(entry.getKey(), entry.getValue().toString());
                                    return document;
                                }
                            })
                            .flatMap(new Func1<JsonDocument, Observable<? extends JsonDocument>>() {
                                @Override
                                public Observable<? extends JsonDocument> call(JsonDocument d) {
                                    return defaultBucket.async().replace(d);
                                }
                            })
                            .retryWhen(new Func1<Observable<? extends Throwable>, Observable<?>>() {
                                           @Override
                                           public Observable<?> call(Observable<? extends Throwable> attempts) {
                                               return attempts.flatMap(new Func1<Throwable, Observable<? extends Long>>() {
                                                   @Override
                                                   public Observable<? extends Long> call(Throwable e) {
                                                       if (!(e instanceof CASMismatchException)) {
                                                           return Observable.error(e);
                                                       }
                                                       return Observable.timer(1, TimeUnit.MILLISECONDS);
                                                   }
                                               });
                                           }
                                       }
                            )
                            .subscribe(new Action1<JsonDocument>() {
                                @Override
                                public void call(JsonDocument updated) {
                                    System.out.println("Updated: " + updated.id());
                                }
                            });
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
        return OK;
    }

    @Override
    public int insert(String table, String key, Map<String, ByteIterator> values) {
        JsonObject content;
        key = createQualifiedKey(table, key);
        try {
            Iterator<Map.Entry<String, ByteIterator>> entries = values.entrySet().iterator();
            content = JsonObject.empty();
            while (entries.hasNext()) {
                Map.Entry<String, ByteIterator> entry = entries.next();
                content.put(entry.getKey(), entry.getValue().toString());
            }

        } catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
        JsonDocument document = JsonDocument.create(key, objectExpirationTime, content);
        defaultBucket.upsert(document);
        return OK;
    }

    @Override
    public int delete(String table, String key) {
        key = createQualifiedKey(table, key);
        try {
            defaultBucket.remove(key);
            return OK;
        } catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
    }
}
