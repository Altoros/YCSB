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
import java.net.UnknownHostException;
import java.util.*;
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
public class MongoDbClient2_13 extends DB {

    protected final MongoConfig mongoConfig = new MongoConfig(getProperties());

    /** A singleton Mongo instance. */
    private static MongoClient mongoClient;

    /** The default write concern for the test. */
    private static WriteConcern writeConcern;

    /** The default read preference for the test */
    private static ReadPreference readPreference;

    /** The database to access. */
    private static String database;

    private static Random random = new Random();

    /**
     * Initialize any state for this DB.
     * Called once per DB instance; there is one DB instance per client thread.
     */
    @Override
    public void init() throws DBException {
        String urlParam = mongoConfig.getHosts();
        database = mongoConfig.getDatabase();

        try {
            String[] clients = urlParam.split(",");
            List<ServerAddress> seeds = new ArrayList<ServerAddress>();
            for (String ob : clients) {
                String url = ob;
                if (url.startsWith("mongodb://")) {
                    url = url.substring(10);
                }
                url += "/" + database;
                try {
                    seeds.add(new DBAddress(url));
                } catch (UnknownHostException e) {
                    System.out.println(e);
                }
            }
            writeConcern = mongoConfig.getWriteConcern();
            readPreference = mongoConfig.getReadPreference();

            MongoClientOptions options = MongoClientOptions.builder()
                    .writeConcern(writeConcern)
                    .readPreference(readPreference)
                    .connectionsPerHost(mongoConfig.getThreadCount())
                    .cursorFinalizerEnabled(false).build();
            mongoClient = new MongoClient(seeds, options);
        } catch (Exception e1) {
            System.err.println("Could not initialize MongoDB connection pool for Loader: " + e1.toString());
            e1.printStackTrace();
            return;
        }

    }
    /**
     * Cleanup any state for this DB.
     * Called once per DB instance; there is one DB instance per client thread.
     */
    @Override
    public void cleanup() throws DBException {
        mongoClient.close();
    }

    /**
     * Delete a record from the database.
     *
     * @param table The name of the table
     * @param key The record key of the record to delete.
     * @return Zero on success, a non-zero error code on error. See this class's description for a discussion of error codes.
     */
    @Override
    public int delete(String table, String key) {
        com.mongodb.DB db = null;
        try {
            db = mongoClient.getDB(database);
            DBCollection collection = db.getCollection(table);
            DBObject q = new BasicDBObject().append("_id", key);
            WriteResult res = collection.remove(q, writeConcern);
            return OK;
        }
        catch (Exception e) {
            System.err.println(e.toString());
            return ERROR;
        }
        finally {
        }
    }

    @Override
    /**
     * Insert a record in the database. Any field/value pairs in the specified values HashMap will be written into the record with the specified
     * record key.
     *
     * @param table The name of the table
     * @param key The record key of the record to insert.
     * @param values A HashMap of field/value pairs to insert in the record
     * @return Zero on success, a non-zero error code on error. See this class's description for a discussion of error codes.
     */
    public int insert(String table, String key, Map<String, ByteIterator> values) {
        com.mongodb.DB db;
        try {
            db = mongoClient.getDB(database);
            DBCollection collection = db.getCollection(table);
            DBObject r = new BasicDBObject().append("_id", key);
            for (String k : values.keySet()) {
                r.put(k, values.get(k).toArray());
            }
            WriteResult res = collection.insert(r, writeConcern);
            return OK;
        }
        catch (Exception e) {
            e.printStackTrace();
            return ERROR;
        }
        finally {
        }
    }

    @Override
    @SuppressWarnings("unchecked")
    /**
     * Read a record from the database. Each field/value pair from the result will be stored in a Map.
     *
     * @param table The name of the table
     * @param key The record key of the record to read.
     * @param field The field to read
     * @param result A Map of field/value pairs for the result
     * @return Zero on success, a non-zero error code on error or "not found".
     */
    public int readOne(String table, String key, String field, Map<String,ByteIterator> result) {

        DBObject fieldsToReturn = new BasicDBObject();
        fieldsToReturn.put(field, 1);

        return read(table, key, result, fieldsToReturn);
    }

    @Override
    @SuppressWarnings("unchecked")
    /**
     * Read a record from the database. Each field/value pair from the result will be stored in a Map.
     *
     * @param table The name of the table
     * @param key The record key of the record to read.
     * @param result A Map of field/value pairs for the result
     * @return Zero on success, a non-zero error code on error or "not found".
     */
    public int readAll(String table, String key, Map<String,ByteIterator> result) {
        return read(table, key, result, null);
    }


    public int read(String table, String key, Map<String, ByteIterator> result,
            DBObject fieldsToReturn) {
        com.mongodb.DB db;
        try {
            db = mongoClient.getDB(database);

            DBCollection collection = db.getCollection(table);
            DBObject q = new BasicDBObject().append("_id", key);
            DBObject queryResult = collection.findOne(q, fieldsToReturn, readPreference);

            if (queryResult != null) {
                result.putAll(resultify(queryResult));
            }
            return queryResult != null ? OK : ERROR;
        } catch (Exception e) {
            System.err.println(e.toString());
            return ERROR;
        } finally {
        }
    }

    @Override
    /**
     * Update a record in the database. Any field/value pairs in the specified values Map will be written into the record with the specified
     * record key, overwriting any existing values with the same field name.
     *
     * @param table The name of the table
     * @param key The record key of the record to write.
     * @param value The value to update in the key record
     * @return Zero on success, a non-zero error code on error.  See this class's description for a discussion of error codes.
     */
    public int updateOne(String table, String key, String field, ByteIterator value) {

        DBObject fieldsToSet = new BasicDBObject();
        fieldsToSet.put(key, value.toArray());

        return update(table, key, fieldsToSet);
    }

    /**
     * Update a record in the database. Any field/value pairs in the specified values Map will be written into the record with the specified
     * record key, overwriting any existing values with the same field name.
     *
     * @param table The name of the table
     * @param key The record key of the record to write.
     * @param values A Map of field/value pairs to update in the record
     * @return Zero on success, a non-zero error code on error.  See this class's description for a discussion of error codes.
     */
    public int updateAll(String table, String key, Map<String,ByteIterator> values) {

        DBObject fieldsToSet = new BasicDBObject();
        Iterator<String> keys = values.keySet().iterator();
        while (keys.hasNext()) {
            String tmpKey = keys.next();
            fieldsToSet.put(tmpKey, values.get(tmpKey).toArray());
        }

        return update(table, key, fieldsToSet);
    }

    public int update(String table, String key, DBObject fieldsToSet) {
        com.mongodb.DB db = null;
        try {
            db = mongoClient.getDB(database);

            DBCollection collection = db.getCollection(table);
            DBObject q = new BasicDBObject().append("_id", key);
            DBObject u = new BasicDBObject();

            u.put("$set", fieldsToSet);
            WriteResult res = collection.update(q, u, false, false,
                    writeConcern);
            return OK;
        } catch (Exception e) {
            System.err.println(e.toString());
            return ERROR;
        } finally {
        }
    }

    @Override
    @SuppressWarnings("unchecked")
    /**
     * Perform a range scan for a set of records in the database. Each field/value pair from the result will be stored in a Map.
     *
     * @param table The name of the table
     * @param startkey The record key of the first record to read.
     * @param recordcount The number of records to read
     * @param result A List of Maps, where each Map is a set field/value pairs for one record
     * @return Zero on success, a non-zero error code on error.  See this class's description for a discussion of error codes.
     */
    public int scanAll(String table, String startkey, int recordcount, List<Map<String, ByteIterator>> result) {

        return scan(table, startkey, recordcount, result);
    }

    @Override
    @SuppressWarnings("unchecked")
    /**
     * Perform a range scan for a set of records in the database. Each field/value pair from the result will be stored in a Map.
     *
     * @param table The name of the table
     * @param startkey The record key of the first record to read.
     * @param recordcount The number of records to read
     * @param field The field to read
     * @param result A List of Maps, where each Map is a set field/value pairs for one record
     * @return Zero on success, a non-zero error code on error.  See this class's description for a discussion of error codes.
     */
    public int scanOne(String table, String startkey, int recordcount, String field, List<Map<String, ByteIterator>> result) {

        return scan(table, startkey, recordcount, result);
    }

    public int scan(String table, String startkey, int recordcount,
            List<Map<String, ByteIterator>> result) {
        com.mongodb.DB db = null;
        DBCursor cursor = null;
        try {
            db = mongoClient.getDB(database);
            DBCollection collection = db.getCollection(table);
            // { "_id":{"$gte":startKey, "$lte":{"appId":key+"\uFFFF"}} }
            DBObject scanRange = new BasicDBObject().append("$gte", startkey);
            DBObject q = new BasicDBObject().append("_id", scanRange);
            cursor = collection.find(q).limit(recordcount);    //TODO: apply readPreference here
            while (cursor.hasNext()) {
                result.add(resultify(cursor.next()));
            }

            return OK;
        } catch (Exception e) {
            System.err.println(e.toString());
            return ERROR;
        }
        finally
        {

        }

    }

    @Override
    @SuppressWarnings("unchecked")
    /**
     * Perform a range scan for a set of records in the database. Each field/value pair from the result will be stored in a HashMap.
     *
     * @param table The name of the table
     * @param key The record key of the first record to read.
     * @param limit The number of records to read
     * @return Zero on success, a non-zero error code on error. See this class's description for a discussion of error codes.
     */
    public int query(String table, String key, int limit) {
        int startIndex = random.nextInt(9);
        String field = "field" + startIndex;

        try {
            key = field + key.substring(4 + startIndex, 12 + startIndex);
        } catch (StringIndexOutOfBoundsException e) {
            key = field;
        }

        com.mongodb.DB db = null;
        DBCursor cursor = null;
        try {
            db = mongoClient.getDB(database);
            DBCollection collection = db.getCollection(table);
            DBObject query = QueryBuilder.start(field).greaterThanEquals(key).get();
            cursor = collection.find(query, null).limit(limit);
            while(cursor.hasNext()) {
                cursor.next().toMap();
            }
            return OK;
        } catch (Exception e) {
            return ERROR;
        } finally {
            if (cursor != null) {
                cursor.close();
            }
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

