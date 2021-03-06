package com.yahoo.ycsb.db;

import com.datastax.driver.core.*;
import com.datastax.driver.core.querybuilder.Insert;
import com.datastax.driver.core.querybuilder.QueryBuilder;
import com.datastax.driver.core.querybuilder.Select;
import com.yahoo.ycsb.*;

import java.nio.ByteBuffer;

import java.util.*;

/**
 * Tested with Cassandra 2.0, CQL client for YCSB framework
 * <p/>
 * In CQLSH, create keyspace and table.  Something like:
 * <p/>
 * create keyspace ycsb WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor': 1 };
 * create table ycsb.usertable (
 * y_id varchar primary key,
 * field0 blob,
 * field1 blob,
 * field2 blob,
 * field3 blob,
 * field4 blob,
 * field5 blob,
 * field6 blob,
 * field7 blob,
 * field8 blob,
 * field9 blob);
 *
 * @author cmatser
 * @author Serj Sintsov ssivikt[at]gmail.com
 */
public class CassandraCQLClient extends DB {

    private static volatile SharedCluster sharedCluster;
    private CassandraDescriptor descriptor;

    private static class SharedCluster {
        final CassandraDescriptor descr;

        final Cluster cluster;
        final Session session;

        final PreparedStatement deleteStatement;
        final PreparedStatement selectStatement;
        final Map<String, PreparedStatement> selectStatements;
        final PreparedStatement scanStatement;
        final Map<String, PreparedStatement> scanStatements;
        final PreparedStatement insertStatement;
        final Map<String, PreparedStatement> updateStatements;

        private SharedCluster(Properties props) throws DBException {
            log("Start initialization");

            descr = new CassandraDescriptor(props);
            logDebug("Config to be used: ");
            logDebug(descr.toString());

            try {
                Cluster.Builder builder = Cluster.builder()
                        .withPort(descr.getPort())
                        .withPoolingOptions(buildPoolingOptions())
                        .withSocketOptions(buildSocketOptions())
                        .addContactPoints(descr.getHosts());

                if (descr.getUsername() != null)
                    builder = builder.withCredentials(descr.getUsername(), descr.getPassword());

                cluster = builder.build();

                Metadata metadata = cluster.getMetadata();
                System.out.printf("Connected to cluster: %s\n", metadata.getClusterName());

                for (Host discoveredHost : metadata.getAllHosts()) {
                    System.out.printf("Datacenter: %s; Host: %s; Rack: %s\n",
                            discoveredHost.getDatacenter(),
                            discoveredHost.getAddress(),
                            discoveredHost.getRack());
                }

                session = cluster.connect(descr.getKeyspace());

                deleteStatement = buildDeleteStatement();
                logDebug("Delete statement: " + deleteStatement.getQueryString());

                insertStatement = buildInsertStatement();
                logDebug("Insert statement: " + insertStatement.getQueryString());

                updateStatements = buildUpdateStatements();
                logDebug("Update statements: " + stmtToString(updateStatements));

                scanStatement = buildScanStatement();
                logDebug("Scan statement: " + scanStatement.getQueryString());

                scanStatements = buildScanStatements();
                logDebug("Scan statements: " + stmtToString(scanStatements));

                selectStatement = buildSelectStatement();
                logDebug("Select statement: " + selectStatement.getQueryString());

                selectStatements = buildSelectStatements();
                logDebug("Select statements: " + stmtToString(selectStatements));

                log("End initialization");
            }
            catch (Exception e) {
                throw new DBException(e);
            }
        }

        private String stmtToString(Map<String, PreparedStatement> statements) {
            StringBuilder buf = new StringBuilder();

            Iterator<String> keys = statements.keySet().iterator();
            if (keys.hasNext())
                buf.append(statements.get(keys.next()).getQueryString());

            while (keys.hasNext()) {
                buf.append("\n");
                buf.append(statements.get(keys.next()).getQueryString());
            }

            return buf.toString();
        }

        private PoolingOptions buildPoolingOptions() {
            PoolingOptions po = new PoolingOptions();
            po.setMaxConnectionsPerHost(HostDistance.REMOTE, descr.getMaxConnectionsPerHost());
            po.setCoreConnectionsPerHost(HostDistance.REMOTE, descr.getCoreConnectionsPerHost());
            return po;
        }

        private SocketOptions buildSocketOptions() {
            SocketOptions so = new SocketOptions();
            so.setReadTimeoutMillis(descr.getSocketReadTimeoutMillis());
            return so;
        }

        private PreparedStatement buildInsertStatement() {
            Insert is = QueryBuilder.insertInto(descr.getTable());
            is.value(descr.getKeyName(), QueryBuilder.bindMarker());

            for (int i = 0; i < descr.getSecondaryFieldCount(); i++)
                is.value(descr.getFieldPrefix() + i, QueryBuilder.bindMarker());

            PreparedStatement insertStatement = session.prepare(is);
            insertStatement.setConsistencyLevel(descr.getWriteConsistencyLevel());

            return insertStatement;
        }

        private Map<String, PreparedStatement> buildUpdateStatements() {
            Insert is = QueryBuilder.insertInto(descr.getTable());
            is.value(descr.getKeyName(), QueryBuilder.bindMarker());

            for (int i = 0; i < descr.getSecondaryFieldCount(); i++)
                is.value(descr.getFieldPrefix() + i, QueryBuilder.bindMarker());

            Map<String, PreparedStatement> updateStatements = new HashMap<>(descr.getSecondaryFieldCount());

            for (int i = 0; i < descr.getSecondaryFieldCount(); i++) {
                is = QueryBuilder.insertInto(descr.getTable());
                is.value(descr.getKeyName(), QueryBuilder.bindMarker());
                is.value(descr.getFieldPrefix() + i, QueryBuilder.bindMarker());

                PreparedStatement ps = session.prepare(is);
                ps.setConsistencyLevel(descr.getWriteConsistencyLevel());
                updateStatements.put(descr.getFieldPrefix() + i, ps);
            }

            return updateStatements;
        }

        private PreparedStatement buildDeleteStatement() {
            PreparedStatement deleteStatement = session.prepare(
                    QueryBuilder.delete()
                            .from(descr.getTable())
                            .where(QueryBuilder.eq(descr.getKeyName(), QueryBuilder.bindMarker()))
            );

            deleteStatement.setConsistencyLevel(descr.getWriteConsistencyLevel());

            return deleteStatement;
        }

        private PreparedStatement buildSelectStatement() {
            String ss = QueryBuilder.select()
                    .all()
                    .from(descr.getTable())
                    .where(QueryBuilder.eq(descr.getKeyName(), QueryBuilder.bindMarker()))
                    .getQueryString();

            PreparedStatement selectStatement = session.prepare(ss);
            selectStatement.setConsistencyLevel(descr.getReadConsistencyLevel());
            return selectStatement;
        }

        private Map<String, PreparedStatement> buildSelectStatements() {
            Map<String, PreparedStatement> selectStatements = new HashMap<>(descr.getSecondaryFieldCount());
            for (int i = 0; i < descr.getSecondaryFieldCount(); i++) {
                String ss = QueryBuilder.select(descr.getFieldPrefix() + i)
                        .from(descr.getTable())
                        .where(QueryBuilder.eq(descr.getKeyName(), QueryBuilder.bindMarker()))
                        .limit(1)
                        .getQueryString();

                PreparedStatement ps = session.prepare(ss);
                ps.setConsistencyLevel(descr.getReadConsistencyLevel());
                selectStatements.put(descr.getFieldPrefix() + i, ps);
            }

            return selectStatements;
        }

        private PreparedStatement buildScanStatement() {
            Select initialStmt = QueryBuilder.select()
                    .all()
                    .from(descr.getTable());

            PreparedStatement scanStatement = session.prepare(createScanQueryString(initialStmt));
            scanStatement.setConsistencyLevel(descr.getReadConsistencyLevel());

            return scanStatement;
        }

        private Map<String, PreparedStatement> buildScanStatements() {
            Map<String, PreparedStatement> scanStatements = new HashMap<>(descr.getSecondaryFieldCount());

            for (int i = 0; i < descr.getSecondaryFieldCount(); i++) {
                Select initialStmt = QueryBuilder.select(descr.getFieldPrefix() + i)
                        .from(descr.getTable());

                PreparedStatement ps = session.prepare(createScanQueryString(initialStmt));
                ps.setConsistencyLevel(descr.getReadConsistencyLevel());

                scanStatements.put(descr.getFieldPrefix() + i, ps);
            }

            return scanStatements;
        }

        private String createScanQueryString(Select selectStmt) {
            String stmt = selectStmt.toString();

            return String.format(
                    "%s WHERE %s >= token(%s) LIMIT %s",
                    stmt.substring(0, stmt.length() - 1),
                    QueryBuilder.token(descr.getKeyName()),
                    QueryBuilder.bindMarker(),
                    QueryBuilder.bindMarker()
            );
        }

        private void log(String msg) {
            System.out.println(this + ": " + msg);
        }

        private void logDebug(String msg) {
            if (descr.isDebug())
                System.out.println(this + ": " + msg);
        }
    }

    /**
     * Initialize any state for this DB. Called once per DB instance; there is
     * one DB instance per client thread.
     */
    @Override
    public void init() throws DBException {
        createSharedCluster(getProperties());
        descriptor = sharedCluster.descr;
        logDebug("Initialized");
    }

    private static synchronized SharedCluster createSharedCluster(Properties props) throws DBException {
        if (sharedCluster == null)
            sharedCluster = new SharedCluster(props);
        return sharedCluster;
    }

    /**
     * Cleanup any state for this DB. Called once per DB instance; there is one
     * DB instance per client thread.
     */
    @Override
    public void cleanup() throws DBException { }

    /**
     * Read a record from the database. Each field/value pair from the result will
     * be stored in a Map.
     *
     * @param table  The name of the table
     * @param key    The record key of the record to read.
     * @param result A Map of field/value pairs for the result
     * @return Zero on success, a non-zero error code on error
     */
    @Override
    public int readAll(String table, String key, Map<String, ByteIterator> result) {
        BoundStatement bs = sharedCluster.selectStatement.bind(key);
        return read(key, descriptor.getTotalFieldCount(), result, bs);
    }

    /**
     * Read a record from the database. Each field/value pair from the result will be stored in a Map.
     *
     * @param table  The name of the table
     * @param key    The record key of the record to read.
     * @param field  The field to read
     * @param result A Map of field/value pairs for the result
     * @return Zero on success, a non-zero error code on error
     */
    @Override
    public int readOne(String table, String key, String field, Map<String, ByteIterator> result) {
        BoundStatement bs = sharedCluster.selectStatements.get(field).bind(key);
        return read(key, 2, result, bs);
    }

    private int read(String key, int fieldCount, Map<String, ByteIterator> result, BoundStatement bs) {
        try {
            if (descriptor.isDebug())
                System.out.println(bs.preparedStatement().getQueryString());

            ResultSet rs = sharedCluster.session.execute(bs);
            Row row = rs.one();

            if (row == null) {
                logError("Key " + key + " was not found; did you run a load job with the correct parameters?");
                return ERROR;
            }

            if (row.getColumnDefinitions().size() != fieldCount) {
                logError("Received row " + key + " contains only " + row.getColumnDefinitions().size() + " not " + fieldCount);
                return ERROR;
            }

            for (ColumnDefinitions.Definition def : row.getColumnDefinitions()) {
                ByteBuffer val = row.getBytesUnsafe(def.getName());
                result.put(def.getName(), val == null ? null : new ByteArrayByteIterator(val.array()));
            }

            return OK;
        }
        catch (Exception e) {
            logError("Error reading key: " + key, e);
            return ERROR;
        }
    }

    /**
     * Perform a range scan for a set of records in the database. Each
     * field/value pair from the result will be stored in a Map.
     * <p/>
     * Cassandra CQL uses "token" method for range scan which doesn't always
     * yield intuitive results.
     *
     * @param table       The name of the table
     * @param startkey    The record key of the first record to read.
     * @param recordcount The number of records to read
     * @param field       The field to read
     * @param result      A List of Maps, where each Map is a set
     *                    field/value pairs for one record
     * @return Zero on success, a non-zero error code on error
     */
    @Override
    public int scanOne(String table, String startkey, int recordcount, String field, List<Map<String, ByteIterator>> result) {
        BoundStatement bs = sharedCluster.scanStatements.get(field).bind(startkey, recordcount);
        return scan(startkey, result, bs);
    }

    /**
     * Perform a range scan for a set of records in the database. Each
     * field/value pair from the result will be stored in a Map.
     * <p/>
     * Cassandra CQL uses "token" method for range scan which doesn't always
     * yield intuitive results.
     *
     * @param table       The name of the table
     * @param startkey    The record key of the first record to read.
     * @param recordcount The number of records to read
     * @param result      A List of Maps, where each Map is a set
     *                    field/value pairs for one record
     * @return Zero on success, a non-zero error code on error
     */
    @Override
    public int scanAll(String table, String startkey, int recordcount, List<Map<String, ByteIterator>> result) {
        BoundStatement bs = sharedCluster.scanStatement.bind(startkey, recordcount);
        return scan(startkey, result, bs);
    }

    public int scan(String startkey, List<Map<String, ByteIterator>> result, BoundStatement bs) {
        try {
            if (descriptor.isDebug())
                System.out.println(bs.preparedStatement().getQueryString());

            ResultSet rs = sharedCluster.session.execute(bs);

            for (Row row : rs) {
                HashMap<String, ByteIterator> tuple = new HashMap<>();
                for (ColumnDefinitions.Definition def : row.getColumnDefinitions()) {
                    ByteBuffer val = row.getBytesUnsafe(def.getName());
                    tuple.put(def.getName(), val == null ? null : new ByteArrayByteIterator(val.array()));
                }

                result.add(tuple);
            }

            return OK;
        }
        catch (Exception e) {
            logError("Error scanning with startkey: " + startkey, e);
            return ERROR;
        }
    }

    /**
     * Update a record in the database. Any field/value pairs in the specified values Map will be written into the record with the specified
     * record key, overwriting any existing values with the same field name.
     *
     * @param table The name of the table
     * @param key   The record key of the record to write.
     * @param field The field to update
     * @param value The value to update in the key record
     * @return Zero on success, a non-zero error code on error.
     */
    @Override
    public int updateOne(String table, String key, String field, ByteIterator value) {
        HashMap<String, ByteIterator> values = new HashMap<>();
        values.put(field, value);
        return insert(table, key, values);
    }

    /**
     * Update a record in the database. Any field/value pairs in the specified values Map will be written into the record with the specified
     * record key, overwriting any existing values with the same field name.
     *
     * @param table  The name of the table
     * @param key    The record key of the record to write.
     * @param values A Map of field/value pairs to update in the record
     * @return Zero on success, a non-zero error code on error.
     */
    @Override
    public int updateAll(String table, String key, Map<String, ByteIterator> values) {
        return insert(table, key, values);
    }

    /**
     * Insert a record in the database. Any field/value pairs in the specified
     * values Map will be written into the record with the specified record
     * key.
     *
     * @param table  The name of the table
     * @param key    The record key of the record to insert.
     * @param values A Map of field/value pairs to insert in the record
     * @return Zero on success, a non-zero error code on error
     */
    @Override
    public int insert(String table, String key, Map<String, ByteIterator> values) {
        try {
            Object[] vals = new Object[values.size() + 1];
            vals[0] = key;
            int i = 1;

            for (Map.Entry<String, ByteIterator> entry : values.entrySet())
                vals[i++] = ByteBuffer.wrap(entry.getValue().toArray());

            PreparedStatement stmt = values.size() == 1
                    ? sharedCluster.updateStatements.get(values.keySet().iterator().next())
                    : sharedCluster.insertStatement;

            BoundStatement bs = stmt.bind(vals);

            if (descriptor.isDebug())
                System.out.println(bs.preparedStatement().getQueryString());

            sharedCluster.session.execute(bs);

            return OK;
        }
        catch (Exception e) {
            logError(e);
        }

        return ERROR;
    }

    /**
     * Delete a record from the database.
     *
     * @param table The name of the table
     * @param key   The record key of the record to delete.
     * @return Zero on success, a non-zero error code on error
     */
    @Override
    public int delete(String table, String key) {
        try {
            if (descriptor.isDebug())
                System.out.println(sharedCluster.deleteStatement.getQueryString());

            sharedCluster.session.execute(sharedCluster.deleteStatement.bind(key));

            return OK;
        }
        catch (Exception e) {
            logError("Error deleting key: " + key, e);
        }

        return ERROR;
    }

    private void logError(Exception e) {
        logError(null, e);
    }

    private void logError(String msg) {
        logError(msg, null);
    }

    private void logError(String msg, Exception e) {
        if (e != null)
            e.printStackTrace();

        if (msg != null)
            System.err.println(msg);
    }

    private void logDebug(String msg) {
        if (descriptor.isDebug())
            System.out.println(this + ": " + msg);
    }

}
