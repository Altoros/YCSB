package com.yahoo.ycsb.couchbase;

import com.yahoo.ycsb.config.PropertiesConfig;
import com.yahoo.ycsb.memcached.MemcachedCompatibleConfig;
import net.spy.memcached.FailureMode;
import com.couchbase.client.java.PersistTo;
import com.couchbase.client.java.ReplicateTo;

import java.util.Properties;

public class CouchbaseConfig extends PropertiesConfig implements MemcachedCompatibleConfig {

    public static final String HOSTS_PROPERTY = "couchbase.hosts";

    public static final String BUCKET_PROPERTY = "couchbase.bucket";

    public static final String DEFAULT_BUCKET = "default";

    public static final String USER_PROPERTY = "couchbase.user";

    public static final String PASSWORD_PROPERTY = "couchbase.password";

    public static final String SHUTDOWN_TIMEOUT_MILLIS_PROPERTY = "couchbase.shutdownTimeoutMillis";

    public static final long DEFAULT_SHUTDOWN_TIMEOUT_MILLIS = 30000;

    public static final String OBJECT_EXPIRATION_TIME_PROPERTY = "couchbase.objectExpirationTime";

    public static final int DEFAULT_OBJECT_EXPIRATION_TIME = Integer.MAX_VALUE;

    public static final String CHECK_OPERATION_STATUS_PROPERTY = "couchbase.checkOperationStatus";

    public static final boolean CHECK_OPERATION_STATUS_DEFAULT = true;

    public static final long DEFAULT_OP_TIMEOUT = 60000;

    public static final String OP_TIMEOUT_PROPERTY = "couchbase.opTimeout";

    public static final String READ_BUFFER_SIZE_PROPERTY = "couchbase.readBufferSize";

    public static final int READ_BUFFER_SIZE_DEFAULT = 16384;

    public static final String FAILURE_MODE_PROPERTY = "couchbase.failureMode";

    public static final FailureMode FAILURE_MODE_PROPERTY_DEFAULT = FailureMode.Redistribute;

    public static final String DDOCS_PROPERTY = "couchbase.ddocs";

    public static final String VIEWS_PROPERTY = "couchbase.views";

    public static final String CONCURRENT_UPDATE_RETRY_TIME_MILLIS = "couchbase.concurrentUpdateRetryTimeMillis";

    public static final String UPDATE_TYPE = "couchbase.updateType";

    public static final String PERSIST_TO_PROPERTY = "couchbase.persistTo";
    public static final PersistTo PERSIST_TO_PROPERTY_DEFAULT = PersistTo.MASTER;

    public static final String REPLICATE_TO_PROPERTY = "couchbase.replicateTo";
    public static final ReplicateTo REPLICATE_TO_PROPERTY_DEFAULT = ReplicateTo.ONE;

    private long concurrentUpdateRetryTimeMillis = 5;
    private UpdateType updateType = UpdateType.SYNC_CAS_LOOP;

    public CouchbaseConfig(Properties properties) {
        super(properties);
        declareProperty(HOSTS_PROPERTY, true);
        declareProperty(BUCKET_PROPERTY, true);
        declareProperty(USER_PROPERTY, false);
        declareProperty(PASSWORD_PROPERTY, false);
        declareProperty(CHECK_OPERATION_STATUS_PROPERTY, CHECK_OPERATION_STATUS_DEFAULT);
        declareProperty(OP_TIMEOUT_PROPERTY, DEFAULT_OP_TIMEOUT);
        declareProperty(READ_BUFFER_SIZE_PROPERTY, READ_BUFFER_SIZE_DEFAULT);
        declareProperty(FAILURE_MODE_PROPERTY, FAILURE_MODE_PROPERTY_DEFAULT);
        declareProperty(SHUTDOWN_TIMEOUT_MILLIS_PROPERTY, DEFAULT_SHUTDOWN_TIMEOUT_MILLIS);
        declareProperty(OBJECT_EXPIRATION_TIME_PROPERTY, DEFAULT_OBJECT_EXPIRATION_TIME);
        declareProperty(DDOCS_PROPERTY, false);
        declareProperty(VIEWS_PROPERTY, false);

        Long concurrentUpdateRetryTimeMillis_tmp = getLong(CONCURRENT_UPDATE_RETRY_TIME_MILLIS);
        if (concurrentUpdateRetryTimeMillis_tmp != null)
            concurrentUpdateRetryTimeMillis = concurrentUpdateRetryTimeMillis_tmp;

        String updateType_tmp = getString(UPDATE_TYPE);
        if (updateType_tmp != null)
            updateType = UpdateType.valueOf(updateType_tmp);
    }

    @Override
    public String getHosts() {
        String host = getString(HOSTS_PROPERTY);
        return host;
    }

    public long getConcurrentUpdateRetryTimeMillis() {
        return concurrentUpdateRetryTimeMillis;
    }

    public UpdateType getUpdateType() {
        return updateType;
    }

    public String getBucket() {
        return getString(BUCKET_PROPERTY);
    }

    public String getUser() {
        return getString(USER_PROPERTY);
    }

    public String getPassword() {
        return getString(PASSWORD_PROPERTY);
    }

    @Override
    public boolean getCheckOperationStatus() {
        return getBoolean(CHECK_OPERATION_STATUS_PROPERTY);
    }

    @Override
    public long getOpTimeout() {
        return getLong(OP_TIMEOUT_PROPERTY);
    }

    @Override
    public int getReadBufferSize() {
        return getInteger(READ_BUFFER_SIZE_PROPERTY);
    }

    @Override
    public FailureMode getFailureMode() {
        String failureModeValue = getProperty(FAILURE_MODE_PROPERTY);
        return failureModeValue != null ?
                FailureMode.valueOf(failureModeValue) :
                this.<FailureMode>getDefaultValue(FAILURE_MODE_PROPERTY);
    }

    @Override
    public long getShutdownTimeoutMillis() {
        return getLong(SHUTDOWN_TIMEOUT_MILLIS_PROPERTY);
    }

    @Override
    public int getObjectExpirationTime() {
        return getInteger(OBJECT_EXPIRATION_TIME_PROPERTY);
    }

    public String[] getDdocs() {
        return getString(DDOCS_PROPERTY) != null ? getString(DDOCS_PROPERTY).split(",") : null;
    }

    public String[] getViews() {
        return getString(VIEWS_PROPERTY) != null ? getString(VIEWS_PROPERTY).split(",") : null;
    }

    public PersistTo getPersistTo() {
        String persist =  getString(PERSIST_TO_PROPERTY);
        return persist != null ? PersistTo.valueOf(persist) : PERSIST_TO_PROPERTY_DEFAULT;
    }

    public ReplicateTo getReplicateTo() {
        String replicate =  getString(REPLICATE_TO_PROPERTY);
        return replicate != null ? ReplicateTo.valueOf(replicate) : REPLICATE_TO_PROPERTY_DEFAULT;
    }

    public enum UpdateType {
        SYNC_LOCAL_LOCK,
        SYNC_CAS_LOOP,
        ASYNC_CAS_LOOP
    }
}
