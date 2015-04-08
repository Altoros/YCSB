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

import java.util.*;

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
        public static final Bucket BUCKET = getClusterInstance().openBucket();
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
        Iterator<Map.Entry<String, Integer>> docKeysIt = docUpdateRaces.entrySet().iterator();

        if (docKeysIt.hasNext())
            buf.append(keyUpdateRacesToString(docKeysIt.next()));

        while (docKeysIt.hasNext()) {
            buf.append(keyUpdateRacesToString(docKeysIt.next()));
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
