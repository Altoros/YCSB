/**
 * MongoDB client binding for YCSB.
 *
 * Submitted by Yen Pai on 5/11/2010.
 *
 * https://gist.github.com/000a66b8db2caf42467b#file_mongo_db.java
 *
 */

package com.yahoo.ycsb.db;

import com.mongodb.*;
import com.yahoo.ycsb.ByteArrayByteIterator;
import com.yahoo.ycsb.ByteIterator;
import com.yahoo.ycsb.DB;
import com.yahoo.ycsb.DBException;

import java.io.UnsupportedEncodingException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * MongoDB client for YCSB framework.
 *
 * Properties to set:
 *
 * mongodb.url=mongodb://localhost:27017 mongodb.database=ycsb
 * mongodb.writeConcern=journaled
 *
 * @author ypai
 */
public class MongoDbClient extends DB {

    MongoConfig mongoConfig;

    /** A singleton Mongo instance. */
    private static MongoClient[] mongoClient;

    /** The default write concern for the test. */
    private static WriteConcern writeConcern;

    /** The default read preference for the test */
    private static ReadPreference readPreference;

    /** The database to access. */
    private static com.mongodb.DB[] db;

    private static int serverCounter;

    private static AtomicInteger initCount = new AtomicInteger();

    /**
     * Initialize any state for this DB.
     * Called once per DB instance; there is one DB instance per client JVM.
     */
    @Override
    public void init() throws DBException {
        initCount.incrementAndGet();
        synchronized (MongoDbClient.class) {
            if (mongoClient != null) {
                return;
            }
            mongoConfig = new MongoConfig(getProperties());
            String urlParam = mongoConfig.getHosts();

            System.setProperty("DEBUG.MONGO", "false");
            System.setProperty("DB.TRACE", "false");
            try {
                String[] servers = urlParam.split(",");
                writeConcern = mongoConfig.getWriteConcern();
                readPreference = mongoConfig.getReadPreference();
                MongoClientOptions.Builder builder = MongoClientOptions.builder()
                    .writeConcern(writeConcern)
                    .readPreference(readPreference)
                    .connectionsPerHost(mongoConfig.getThreadCount())
                    .cursorFinalizerEnabled(false);
                mongoClient = new MongoClient[servers.length];
                db = new com.mongodb.DB[servers.length];
                for (int i = 0; i < servers.length; i++) {
                    String url = servers[i];
                    // if mongodb:// prefix is present then this is MongoClientURI format
                    // combine with options to get MongoClient
                    if (url.startsWith("mongodb://")) {
                        MongoClientURI uri = new MongoClientURI(url, builder);
                        mongoClient[i] = new MongoClient(uri);
                    } else {
                        mongoClient[i] = new MongoClient(new ServerAddress(url), builder.build());
                    }
                    db[i] = mongoClient[i].getDB(mongoConfig.getDatabase());
                }
            } catch (Exception e1) {
                System.err.println("Could not initialize Mongo Client: " + e1.toString());
                e1.printStackTrace();
            }
        }
    }

    @Override
    public void cleanup() throws DBException {
        if (initCount.decrementAndGet() == 0) {
            for (MongoClient client : mongoClient) {
                try {
                    client.close();
                } catch (Exception e) {
                    System.err.println("Error while closing mongo client");
                    e.printStackTrace();
                    return;
                }
            }
        }
    }

    @Override
    public int delete(String table, String key) {
        try {
            DBCollection collection = db[serverCounter++ % db.length].getCollection(table);
            DBObject q = new BasicDBObject().append("_id", key);
            WriteResult res = collection.remove(q, writeConcern);
            return OK;
        }
        catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
    }

    @Override
    public int insert(String table, String key, Map<String, ByteIterator> values) {
        try {
            DBCollection collection = db[serverCounter++ % db.length].getCollection(table);

            BasicDBObject doc = new BasicDBObject("_id", key);
            for (String k : values.keySet()) {
                doc.append(k, values.get(k).toArray());
            }
            WriteResult res = collection.insert(doc, writeConcern);
            return OK;
        }
        catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
    }

    @Override
    public int readOne(String table, String key, String field, Map<String,ByteIterator> result) {
        BasicDBObject fieldsToReturn = new BasicDBObject(field, 1);
        return read(table, key, result, fieldsToReturn);
    }

    @Override
    public int readAll(String table, String key, Map<String,ByteIterator> result) {
        return read(table, key, result, null);
    }

    private int read(String table, String key, Map<String, ByteIterator> result, DBObject fieldsToReturn) {
        try {
            DBCollection collection = db[serverCounter++ % db.length].getCollection(table);
            BasicDBObject q = new BasicDBObject("_id", key);
            DBObject queryResult = collection.findOne(q, fieldsToReturn, readPreference);
            if (queryResult != null) {
                result.putAll(resultify(queryResult));
            }
            return queryResult != null ? OK : ERROR;
        } catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
    }

    @Override
    public int updateOne(String table, String key, String field, ByteIterator value) {
        BasicDBObject fieldsToSet = new BasicDBObject(field, value.toArray());
        return update(table, key, fieldsToSet);
    }

    @Override
    public int updateAll(String table, String key, Map<String,ByteIterator> values) {

        BasicDBObject fieldsToSet = new BasicDBObject();
        Iterator<String> keys = values.keySet().iterator();
        while (keys.hasNext()) {
            String tmpKey = keys.next();
            fieldsToSet.append(tmpKey, values.get(tmpKey).toArray());
        }

        return update(table, key, fieldsToSet);
    }

    private int update(String table, String key, DBObject fieldsToSet) {
        try {

            DBCollection collection = db[serverCounter++ % db.length].getCollection(table);

            DBObject q = new BasicDBObject("_id", key);
            BasicDBObject u = new BasicDBObject("$set", fieldsToSet);

            WriteResult res = collection.update(q, u, false, false, writeConcern);
            return OK;
        } catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
    }

    @Override
    public int scanAll(String table, String startkey, int recordcount, List<Map<String, ByteIterator>> result) {
        return scan(table, startkey, recordcount, result);
    }

    @Override
    public int scanOne(String table, String startkey, int recordcount, String field, List<Map<String, ByteIterator>> result) {
        return scan(table, startkey, recordcount, result);
    }

    private int scan(String table, String startkey, int recordcount, List<Map<String, ByteIterator>> result) {
        DBCursor cursor;
        try {
            DBCollection collection = db[serverCounter++ % db.length].getCollection(table);
            DBObject q = new BasicDBObject("_id",  new BasicDBObject("$gte", startkey));
            cursor = new DBCursor(collection, q, null, readPreference);
            while (cursor.hasNext()) {
                result.add(resultify(cursor.next()));
            }

            return OK;
        } catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }

    }

    /**
     * Turn everything in the object into a ByteIterator
     */
    @SuppressWarnings("unchecked")
    private HashMap<String, ByteIterator> resultify(DBObject object) {
        HashMap<String, ByteIterator> decoded = new HashMap<String, ByteIterator>();

        for (Map.Entry<String, Object> entry : ((Map<String, Object>) object.toMap()).entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();
            if (key.equals("_id")) {
                try {
                    decoded.put(key, new ByteArrayByteIterator(((String) value).getBytes("UTF-8")));
                } catch (UnsupportedEncodingException e) {
                    throw new RuntimeException(e);
                }
            }
            else {
                decoded.put(key, new ByteArrayByteIterator((byte[]) value));
            }
        }

        return decoded;
    }
}

