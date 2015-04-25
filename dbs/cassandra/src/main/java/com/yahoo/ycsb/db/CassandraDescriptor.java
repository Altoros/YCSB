package com.yahoo.ycsb.db;

import java.util.Properties;
import com.datastax.driver.core.ConsistencyLevel;
import com.yahoo.ycsb.DBException;
import com.yahoo.ycsb.workloads.CoreWorkload;

public final class CassandraDescriptor {

    private final boolean debug;
    private final String hosts[];
    private final int port;
    private final String username;
    private final String password;
    private final String keyspace;
    private final String keyName;
    private final ConsistencyLevel readConsistencyLevel;
    private final ConsistencyLevel writeConsistencyLevel;
    private final int coreConnectionsPerHost;
    private final int maxConnectionsPerHost;
    private final int socketReadTimeoutMillis;

    private final String table;
    private final int totalFieldCount;
    private final int secondaryFieldCount;
    private final String fieldPrefix;

    public CassandraDescriptor(Properties props) throws DBException{
        CassandraConfig cfg = new CassandraConfig(props);

        debug = cfg.debug;
        username = cfg.username;
        password = cfg.password;

        if (cfg.hosts == null)
            throw missedRequired(CassandraConfig.HOSTS_PROPERTY);
        else
            hosts = cfg.hosts;

        if (cfg.port == null)
            port = 9042;
        else
            port = Integer.parseInt(cfg.port);

        if (cfg.readConsistencyLevel == null)
            readConsistencyLevel = ConsistencyLevel.ONE;
        else
            readConsistencyLevel = ConsistencyLevel.valueOf(cfg.readConsistencyLevel);

        if (cfg.writeConsistencyLevel == null)
            writeConsistencyLevel = ConsistencyLevel.ONE;
        else
            writeConsistencyLevel = ConsistencyLevel.valueOf(cfg.writeConsistencyLevel);

        if (cfg.keyName == null)
            keyName = "y_id";
        else
            keyName = cfg.keyName;

        if (cfg.keyspace == null)
            throw missedRequired(CassandraConfig.KEYSPACE_PROPERTY);
        else
            keyspace = cfg.keyspace;

        if (cfg.coreConnectionsPerHost == null)
            coreConnectionsPerHost = 1;
        else
            coreConnectionsPerHost = Integer.parseInt(cfg.coreConnectionsPerHost);

        if (cfg.maxConnectionsPerHost == null)
            maxConnectionsPerHost = 100;
        else
            maxConnectionsPerHost = Integer.parseInt(cfg.maxConnectionsPerHost);

        if (cfg.socketReadTimeoutMillis == null)
            socketReadTimeoutMillis = 100;
        else
            socketReadTimeoutMillis = Integer.parseInt(cfg.socketReadTimeoutMillis);

        table = props.getProperty(CoreWorkload.TABLENAME_PROPERTY, CoreWorkload.TABLENAME_PROPERTY_DEFAULT);
        secondaryFieldCount = Integer.parseInt(props.getProperty(CoreWorkload.FIELD_COUNT_PROPERTY, CoreWorkload.FIELD_COUNT_PROPERTY_DEFAULT));
        totalFieldCount = secondaryFieldCount + 1;
        fieldPrefix = props.getProperty(CoreWorkload.FIELD_NAME_PREFIX, CoreWorkload.FIELD_NAME_PREFIX_DEFAULT);
    }

    public boolean isDebug() {
        return debug;
    }

    public String[] getHosts() {
        return hosts;
    }

    public int getPort() {
        return port;
    }

    public String getUsername() {
        return username;
    }

    public String getPassword() {
        return password;
    }

    public String getKeyspace() {
        return keyspace;
    }

    public String getKeyName() {
        return keyName;
    }

    public ConsistencyLevel getReadConsistencyLevel() {
        return readConsistencyLevel;
    }

    public ConsistencyLevel getWriteConsistencyLevel() {
        return writeConsistencyLevel;
    }

    public int getCoreConnectionsPerHost() {
        return coreConnectionsPerHost;
    }

    public int getMaxConnectionsPerHost() {
        return maxConnectionsPerHost;
    }

    public int getSocketReadTimeoutMillis() {
        return socketReadTimeoutMillis;
    }

    public String getTable() {
        return table;
    }

    public int getTotalFieldCount() {
        return totalFieldCount;
    }

    public int getSecondaryFieldCount() {
        return secondaryFieldCount;
    }

    public String getFieldPrefix() {
        return fieldPrefix;
    }

    private DBException missedRequired(String name) {
        return new DBException("Required property " + name + " missing for CassandraClient");
    }

    @Override
    public String toString() {
        return getClass() + ": {" +
                "debug=" + debug + "; " +
                "hosts=" + hosts + "; " +
                "port=" + port + "; " +
                "username=" + username + "; " +
                "password=" + password + "; " +
                "keyspace=" + keyspace + "; " +
                "keyName=" + keyName + "; " +
                "readConsistencyLevel=" + readConsistencyLevel + "; " +
                "writeConsistencyLevel=" + writeConsistencyLevel + "; " +
                "coreConnectionsPerHost=" + coreConnectionsPerHost + "; " +
                "maxConnectionsPerHost=" + maxConnectionsPerHost + "; " +
                "socketReadTimeoutMillis=" + socketReadTimeoutMillis + "; " +
                "table=" + table + "; " +
                "totalFieldCount=" + totalFieldCount + "; " +
                "secondaryFieldCount=" + secondaryFieldCount + "; " +
                "fieldPrefix=" + fieldPrefix + "; " + "}";
    }
}
