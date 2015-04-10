package com.yahoo.ycsb.db;

import java.util.Properties;

public class CassandraConfig {

    public static final String HOSTS_PROPERTY = "hosts";
    public static final String PORT_PROPERTY = "hosts";
    public static final String KEYSPACE_PROPERTY = "cassandra.keyspace";
    public static final String KEY_NAME_PROPERTY = "cassandra.keyName";
    public static final String USERNAME_PROPERTY = "cassandra.username";
    public static final String PASSWORD_PROPERTY = "cassandra.password";
    public static final String READ_CONSISTENCY_LEVEL_PROPERTY = "cassandra.readconsistencylevel";
    public static final String WRITE_CONSISTENCY_LEVEL_PROPERTY = "cassandra.writeconsistencylevel";
    public static final String CORE_CONNECTIONS_PER_HOST_PROPERTY = "cassandra.core.connections.per.host";
    public static final String MAX_CONNECTIONS_PER_HOST_PROPERTY = "cassandra.max.connections.per.host";
    public static final String SOCKET_READ_TIMEOUT_PROPERTY = "cassandra.socket.read.timeout.millis";

    public final Boolean debug;
    public final String hosts[];
    public final String port;
    public final String username;
    public final String password;
    public final String keyspace;
    public final String keyName;
    public final String readConsistencyLevel;
    public final String writeConsistencyLevel;
    public final String coreConnectionsPerHost;
    public final String maxConnectionsPerHost;
    public final String socketReadTimeoutMillis;

    public CassandraConfig(Properties props) {
        debug = Boolean.parseBoolean(props.getProperty("debug", "false"));
        hosts = props.getProperty(HOSTS_PROPERTY).split(",");
        port  = props.getProperty(PORT_PROPERTY);
        username = props.getProperty(USERNAME_PROPERTY);
        password = props.getProperty(PASSWORD_PROPERTY);

        keyspace = props.getProperty(KEYSPACE_PROPERTY);
        keyName  = props.getProperty(KEY_NAME_PROPERTY);

        readConsistencyLevel = props.getProperty(READ_CONSISTENCY_LEVEL_PROPERTY);
        writeConsistencyLevel = props.getProperty(WRITE_CONSISTENCY_LEVEL_PROPERTY);

        coreConnectionsPerHost = props.getProperty(CORE_CONNECTIONS_PER_HOST_PROPERTY);
        maxConnectionsPerHost = props.getProperty(MAX_CONNECTIONS_PER_HOST_PROPERTY);
        socketReadTimeoutMillis = props.getProperty(SOCKET_READ_TIMEOUT_PROPERTY);
    }

}
