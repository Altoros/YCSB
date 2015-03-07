package com.yahoo.ycsb.couchbase;

import com.couchbase.client.java.Bucket;
import com.couchbase.client.java.Cluster;
import com.couchbase.client.java.CouchbaseCluster;
import com.couchbase.client.java.document.JsonDocument;
import com.couchbase.client.java.document.json.JsonObject;
import com.yahoo.ycsb.ByteIterator;
import com.yahoo.ycsb.DBException;
import com.yahoo.ycsb.memcached.MemcachedCompatibleClient;
import net.spy.memcached.MemcachedClient;
import net.spy.memcached.PersistTo;
import net.spy.memcached.ReplicateTo;

import java.util.Iterator;
import java.util.Map;
import java.util.Set;

/**
 * Alexei Okhrimenko, 2015
 *
 * this client uses Couchbase Java SDK 2.0.3 and supports Couchbase Server 3.0
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
//            cluster = CouchbaseCluster.create(config.getHosts());
            cluster = getClusterInstance();

            // Open the default bucket
//            defaultBucket = cluster.openBucket();
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
    public int update(String table, String key, Map<String, ByteIterator> values) {
        JsonObject content = null;
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
    public int insert(String table, String key, Map<String, ByteIterator> values) {
        JsonObject content = null;
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
