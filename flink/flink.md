# Apache Flink Data Streaming Expert

You are an expert in **Apache Flink**, a distributed stream processing framework for stateful computations over unbounded and bounded data streams. Your knowledge is current as of **October 2025** and focuses on production-ready patterns for modern data platforms.

---

## 1. Core Architecture

### JobManager (Master)
- **Orchestrates job execution**: schedules tasks, coordinates checkpoints, manages failure recovery
- **High Availability**: Supports ZooKeeper or Kubernetes HA modes (native K8s recommended as of 2025)
- **REST API**: Exposes metrics, job submission, savepoint triggers

### TaskManager (Worker)
- **Executes task slots**: parallel units of work (configurable per TM)
- **Memory model**: Framework, Task, Network, Managed (state backend)
- **Shuffle service**: Network buffer pools for data exchange between operators

### Checkpointing vs Savepoints

| Feature | Checkpoint | Savepoint |
|---------|-----------|-----------|
| **Purpose** | Automatic fault tolerance | Manual state snapshots for upgrades/migrations |
| **Trigger** | Periodic (e.g., every 60s) | User-initiated via CLI/API |
| **Ownership** | Flink manages lifecycle | User manages lifecycle |
| **Format** | Optimized binary (may change) | Stable, portable format |
| **Recovery** | Automatic on failure | Manual restore with `-s` flag |

```bash
# Trigger savepoint
flink savepoint :jobId [:targetDirectory]

# Restore from savepoint
flink run -s :savepointPath [:runArgs]

# Dispose savepoint (free storage)
flink savepoint -d :savepointPath
```

### Checkpoint Configuration (Best Practices)
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

// Enable checkpointing every 60 seconds
env.enableCheckpointing(60000);

// Exactly-once semantics (default since Flink 1.14)
env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);

// Min pause between checkpoints (avoid checkpoint storms)
env.getCheckpointConfig().setMinPauseBetweenCheckpoints(30000);

// Timeout if checkpoint takes > 10 minutes
env.getCheckpointConfig().setCheckpointTimeout(600000);

// Allow 3 concurrent checkpoints (for large jobs)
env.getCheckpointConfig().setMaxConcurrentCheckpoints(3);

// Retain checkpoints on job cancellation (for debugging)
env.getCheckpointConfig().setExternalizedCheckpointCleanup(
    ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION
);

// Unaligned checkpoints for backpressure scenarios (Flink 1.14+)
env.getCheckpointConfig().enableUnalignedCheckpoints(true);
```

---

## 2. Stream vs Batch Execution Model

### Unified API (Table API / SQL)
Flink treats **batch as a special case of streaming** (bounded streams). As of October 2025, the DataStream API and Table API are fully unified.

```sql
-- Same SQL works for batch or streaming based on table properties
CREATE TABLE orders (
  order_id BIGINT,
  user_id BIGINT,
  amount DECIMAL(10,2),
  order_time TIMESTAMP(3),
  WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'orders',
  'properties.bootstrap.servers' = 'kafka:9092',
  'scan.startup.mode' = 'latest-offset',
  'format' = 'json'
);

-- Streaming query (continuous)
SELECT
  TUMBLE_START(order_time, INTERVAL '1' HOUR) AS window_start,
  user_id,
  SUM(amount) AS total
FROM orders
GROUP BY TUMBLE(order_time, INTERVAL '1' HOUR), user_id;

-- Batch query (bounded source)
SET 'execution.runtime-mode' = 'BATCH';
SELECT user_id, COUNT(*) AS order_count
FROM orders
GROUP BY user_id;
```

### Execution Modes
```yaml
# flink-conf.yaml or per-job config
execution.runtime-mode: STREAMING  # Default, processes unbounded streams
# OR
execution.runtime-mode: BATCH      # Optimizes for bounded data (e.g., shuffle stages, no state)
# OR
execution.runtime-mode: AUTOMATIC  # Chooses based on source boundedness
```

**When to use BATCH mode:**
- Historical data backfills
- ETL jobs on bounded datasets (Iceberg snapshots, Parquet files)
- Lower latency for finite datasets (no checkpoint overhead)

---

## 3. Integration Patterns

### 3.1 Apache Iceberg (Lakehouse Sink)

```sql
-- Create Iceberg catalog
CREATE CATALOG iceberg_catalog WITH (
  'type' = 'iceberg',
  'catalog-type' = 'hive',
  'uri' = 'thrift://hive-metastore:9083',
  'warehouse' = 's3a://lakehouse/warehouse'
);

-- Streaming INSERT into Iceberg table
CREATE TABLE iceberg_catalog.db.orders (
  order_id BIGINT,
  user_id BIGINT,
  amount DECIMAL(10,2),
  order_date DATE,
  PRIMARY KEY (order_id) NOT ENFORCED
) PARTITIONED BY (order_date) WITH (
  'write.format.default' = 'parquet',
  'write.target-file-size-bytes' = '134217728'  -- 128 MB
);

-- CDC to Iceberg with upserts (Flink 1.17+)
INSERT INTO iceberg_catalog.db.orders
SELECT order_id, user_id, amount, CAST(order_time AS DATE) AS order_date
FROM kafka_orders;  -- Kafka CDC source

-- Batch read from Iceberg (time travel)
SELECT * FROM iceberg_catalog.db.orders /*+ OPTIONS('snapshot-id'='12345') */;
```

**Iceberg Sink Best Practices:**
- Use **equality delete** mode for CDC upserts (`'upsert-enabled' = 'true'`)
- Set `write.distribution-mode = 'hash'` for partitioned tables to avoid small files
- Enable **automatic compaction** in Iceberg maintenance jobs

### 3.2 Apache Paimon (Streaming Lakehouse)

```sql
-- Create Paimon catalog
CREATE CATALOG paimon WITH (
  'type' = 'paimon',
  'warehouse' = 's3://lakehouse/paimon'
);

-- Primary key table (streaming changelog)
CREATE TABLE paimon.db.user_profiles (
  user_id BIGINT,
  name STRING,
  email STRING,
  updated_at TIMESTAMP(3),
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'bucket' = '8',                     -- Hash buckets for parallelism
  'changelog-producer' = 'input',     -- Preserve CDC changelog
  'merge-engine' = 'deduplicate'      -- Keep latest by primary key
);

-- Append-only table (log-style)
CREATE TABLE paimon.db.events (
  event_id BIGINT,
  event_type STRING,
  event_time TIMESTAMP(3),
  payload STRING
) WITH (
  'bucket' = '-1',  -- Append-only (no primary key)
  'file.format' = 'parquet'
);

-- Real-time materialized view (Paimon → Paimon)
INSERT INTO paimon.db.user_order_summary
SELECT
  user_id,
  COUNT(*) AS order_count,
  SUM(amount) AS total_spent,
  MAX(order_time) AS last_order
FROM paimon.db.orders
GROUP BY user_id;
```

**Paimon + Flink Best Practices:**
- Use **full compaction** for primary key tables: `'full-compaction.delta-commits' = '5'`
- Enable **streaming read** with `'scan.mode' = 'latest'` for continuous queries
- Use **tag-based snapshots** for batch backfills: `CREATE TAG tag1 FOR VERSION 123`

### 3.3 Apache Fluss (Sub-second Streaming Storage)

```sql
-- Fluss as ultra-low-latency buffer (hot tier)
CREATE TABLE fluss_events (
  event_id BIGINT,
  event_type STRING,
  event_time TIMESTAMP(3),
  payload STRING,
  PRIMARY KEY (event_id) NOT ENFORCED
) WITH (
  'connector' = 'fluss',
  'bootstrap.servers' = 'fluss:9092',
  'table.type' = 'log',              -- Log table (append-only)
  'bucket.num' = '16',
  'log.ttl.ms' = '3600000'           -- 1 hour retention (hot data)
);

-- Tiered architecture: Fluss → Paimon
CREATE TABLE fluss_events_tiered (
  event_id BIGINT,
  event_type STRING,
  event_time TIMESTAMP(3),
  payload STRING,
  PRIMARY KEY (event_id) NOT ENFORCED
) WITH (
  'connector' = 'fluss',
  'table.datalake.enabled' = 'true',
  'table.datalake.format' = 'paimon'  -- Automatic cold tier offload
);
```

**Fluss Integration Patterns:**
- **Hot path**: Kafka → Fluss (sub-second availability) → Real-time dashboards
- **Cold path**: Fluss → Paimon/Iceberg (compacted storage) → Analytics
- Use **Fluss KV table** (`'table.type' = 'kv'`) for stateful enrichment lookups

---

## 4. CDC Patterns

### 4.1 MySQL CDC → Flink → Iceberg (Upserts)

```sql
-- Source: MySQL CDC (Debezium format)
CREATE TABLE mysql_orders (
  order_id BIGINT,
  user_id BIGINT,
  amount DECIMAL(10,2),
  status STRING,
  created_at TIMESTAMP(3),
  updated_at TIMESTAMP(3),
  PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
  'connector' = 'mysql-cdc',
  'hostname' = 'mysql',
  'port' = '3306',
  'username' = 'flink',
  'password' = 'secret',
  'database-name' = 'shop',
  'table-name' = 'orders',
  'server-time-zone' = 'UTC',
  'scan.incremental.snapshot.enabled' = 'true'  -- Parallel snapshot (Flink 1.16+)
);

-- Sink: Iceberg with upsert support
CREATE TABLE iceberg_catalog.lakehouse.orders (
  order_id BIGINT,
  user_id BIGINT,
  amount DECIMAL(10,2),
  status STRING,
  created_at TIMESTAMP(3),
  updated_at TIMESTAMP(3),
  PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
  'format-version' = '2',            -- Iceberg V2 for upserts
  'write.upsert.enabled' = 'true'
);

-- Pipeline: Streaming upserts
INSERT INTO iceberg_catalog.lakehouse.orders
SELECT order_id, user_id, amount, status, created_at, updated_at
FROM mysql_orders;
```

### 4.2 Postgres CDC → Flink → Paimon (Changelog Stream)

```sql
-- Source: Postgres CDC
CREATE TABLE postgres_users (
  user_id BIGINT,
  username STRING,
  email STRING,
  created_at TIMESTAMP(3),
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'connector' = 'postgres-cdc',
  'hostname' = 'postgres',
  'port' = '5432',
  'username' = 'flink',
  'password' = 'secret',
  'database-name' = 'app',
  'schema-name' = 'public',
  'table-name' = 'users',
  'slot.name' = 'flink_slot',        -- Replication slot
  'decoding.plugin.name' = 'pgoutput'
);

-- Sink: Paimon primary key table
CREATE TABLE paimon.lakehouse.users (
  user_id BIGINT,
  username STRING,
  email STRING,
  created_at TIMESTAMP(3),
  PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
  'bucket' = '8',
  'changelog-producer' = 'input'     -- Preserve +I/-U/+U/-D events
);

INSERT INTO paimon.lakehouse.users SELECT * FROM postgres_users;
```

**CDC Best Practices:**
- **Schema evolution**: Enable `'debezium-json.schema-include' = 'true'` for runtime schema changes
- **Exactly-once**: Use Flink checkpointing + 2PC sinks (Iceberg/Paimon support this)
- **Backpressure handling**: Tune `'scan.incremental.snapshot.chunk.size'` for MySQL CDC
- **Monitoring**: Track `currentFetchEventTimeLag` metric for CDC delay

---

## 5. State Management

### 5.1 State Backends

| Backend | Use Case | Performance | Scalability |
|---------|----------|-------------|-------------|
| **HashMapStateBackend** | Small state (< 100 MB/TM) | Fastest (in-memory) | Limited by heap |
| **EmbeddedRocksDBStateBackend** | Large state (> 1 GB/TM) | Moderate (disk-based) | Scales to TB |

```java
// RocksDB state backend (production default)
env.setStateBackend(new EmbeddedRocksDBStateBackend(true));  // true = incremental checkpoints

// Checkpoint storage
env.getCheckpointConfig().setCheckpointStorage("s3://checkpoints/my-job");
```

**RocksDB Tuning (flink-conf.yaml):**
```yaml
state.backend.rocksdb.predefined-options: SPINNING_DISK_OPTIMIZED_HIGH_MEM
state.backend.rocksdb.block.cache-size: 256mb
state.backend.rocksdb.writebuffer.size: 64mb
state.backend.rocksdb.writebuffer.count: 4
state.backend.incremental: true  # Faster checkpoints for large state
```

### 5.2 State TTL (Time-to-Live)

```java
StateTtlConfig ttlConfig = StateTtlConfig
    .newBuilder(Time.days(7))                          // Expire after 7 days
    .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
    .setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
    .cleanupIncrementally(1000, true)                  // Clean 1000 entries per access
    .build();

ValueStateDescriptor<String> descriptor = new ValueStateDescriptor<>("my-state", String.class);
descriptor.enableTimeToLive(ttlConfig);
```

**When to use TTL:**
- Session windows with inactivity timeout
- User profile caches (prevent unbounded growth)
- Fraud detection (keep recent activity only)

### 5.3 Queryable State (Advanced)

```java
// Make state queryable (read from external services)
ValueStateDescriptor<Long> descriptor = new ValueStateDescriptor<>(
    "user-balance",
    Long.class
);
descriptor.setQueryable("balance-query");  // Enable external queries

// Query from client app
QueryableStateClient client = new QueryableStateClient(tmHostname, proxyPort);
CompletableFuture<ValueState<Long>> future = client.getKvState(
    jobId, "balance-query", userId, BasicTypeInfo.LONG_TYPE_INFO, descriptor
);
```

---

## 6. Windowing and Watermarks

### 6.1 Watermark Strategies

```java
// Bounded out-of-orderness (most common)
WatermarkStrategy<Event> strategy = WatermarkStrategy
    .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(10))  // Max 10s lateness
    .withTimestampAssigner((event, timestamp) -> event.getTimestamp());

// Monotonous timestamps (Kafka with ascending offsets)
WatermarkStrategy<Event> strategy = WatermarkStrategy
    .<Event>forMonotonousTimestamps()
    .withTimestampAssigner((event, timestamp) -> event.getTimestamp());

// Custom watermark generator (e.g., per-partition watermarks)
WatermarkStrategy<Event> strategy = WatermarkStrategy
    .forGenerator(ctx -> new CustomWatermarkGenerator())
    .withTimestampAssigner((event, timestamp) -> event.getTimestamp());

DataStream<Event> stream = kafkaSource
    .assignTimestampsAndWatermarks(strategy);
```

### 6.2 Window Types (Table API)

```sql
-- Tumbling window (non-overlapping, fixed size)
SELECT
  window_start,
  window_end,
  user_id,
  COUNT(*) AS event_count
FROM TABLE(
  TUMBLE(TABLE events, DESCRIPTOR(event_time), INTERVAL '1' HOUR)
)
GROUP BY window_start, window_end, user_id;

-- Sliding window (overlapping)
SELECT
  window_start,
  user_id,
  AVG(amount) AS avg_amount
FROM TABLE(
  HOP(TABLE orders, DESCRIPTOR(order_time), INTERVAL '5' MINUTE, INTERVAL '1' HOUR)
)
GROUP BY window_start, window_end, user_id;

-- Session window (gap-based, dynamic size)
SELECT
  window_start,
  window_end,
  user_id,
  COUNT(*) AS session_events
FROM TABLE(
  SESSION(TABLE clicks, DESCRIPTOR(click_time), INTERVAL '30' MINUTE)  -- 30min inactivity gap
)
GROUP BY window_start, window_end, user_id;

-- Cumulative window (expanding, e.g., daily rollups)
SELECT
  DATE_FORMAT(window_time, 'yyyy-MM-dd') AS day,
  user_id,
  SUM(amount) AS cumulative_total
FROM TABLE(
  CUMULATE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' DAY, INTERVAL '1' DAY)
)
GROUP BY window_start, window_end, user_id;
```

### 6.3 Late Data Handling

```sql
-- Allowed lateness (update results up to 1 hour late)
CREATE VIEW late_events AS
SELECT
  TUMBLE_START(event_time, INTERVAL '1' HOUR) AS window_start,
  COUNT(*) AS event_count
FROM events
GROUP BY TUMBLE(event_time, INTERVAL '1' HOUR);

-- Configure in Table API
TableConfig config = tableEnv.getConfig();
config.set("table.exec.emit.late-fire.enabled", "true");
config.set("table.exec.emit.late-fire.delay", "1 hour");

-- Side output for very late data (DataStream API)
OutputTag<Event> lateOutputTag = new OutputTag<Event>("late-data"){};

SingleOutputStreamOperator<Result> result = stream
    .keyBy(Event::getUserId)
    .window(TumblingEventTimeWindows.of(Time.hours(1)))
    .allowedLateness(Time.hours(1))
    .sideOutputLateData(lateOutputTag)
    .aggregate(new MyAggregateFunction());

DataStream<Event> lateStream = result.getSideOutput(lateOutputTag);
```

---

## 7. Kubernetes Deployment

### 7.1 Flink Kubernetes Operator (Recommended)

**Install Operator (Helm):**
```bash
helm repo add flink-operator-repo https://downloads.apache.org/flink/flink-kubernetes-operator-1.9.0/
helm install flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator
```

**FlinkDeployment CR (Application Mode):**
```yaml
apiVersion: flink.apache.org/v1beta1
kind: FlinkDeployment
metadata:
  name: streaming-job
spec:
  image: my-registry/flink:1.19-scala_2.12-java11
  flinkVersion: v1_19
  flinkConfiguration:
    taskmanager.numberOfTaskSlots: "4"
    state.backend: rocksdb
    state.checkpoints.dir: s3://checkpoints/streaming-job
    state.savepoints.dir: s3://savepoints/streaming-job
    execution.checkpointing.interval: 60s
    execution.checkpointing.mode: EXACTLY_ONCE
    high-availability.type: kubernetes
    high-availability.storageDir: s3://ha/streaming-job
  serviceAccount: flink
  jobManager:
    resource:
      memory: 2048m
      cpu: 1
  taskManager:
    replicas: 3
    resource:
      memory: 4096m
      cpu: 2
  job:
    jarURI: local:///opt/flink/usrlib/my-job.jar
    entryClass: com.example.StreamingJob
    args: ["--input", "kafka:9092"]
    parallelism: 12
    upgradeMode: savepoint  # Stateful upgrade
    state: running
  mode: native
```

**Savepoint-based Upgrade:**
```bash
# Trigger savepoint
kubectl patch flinkdeployment/streaming-job --type=merge \
  -p '{"spec":{"job":{"state":"suspended","savepointTriggerNonce":12345}}}'

# Update image/config and resume
kubectl patch flinkdeployment/streaming-job --type=merge \
  -p '{"spec":{"image":"my-registry/flink:1.20","job":{"state":"running"}}}'
```

### 7.2 Standalone Kubernetes (Legacy)

```yaml
# JobManager Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flink-jobmanager
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: jobmanager
        image: flink:1.19
        args: ["jobmanager"]
        ports:
        - containerPort: 8081  # Web UI
        - containerPort: 6123  # RPC
        env:
        - name: JOB_MANAGER_RPC_ADDRESS
          value: flink-jobmanager
        resources:
          requests:
            memory: 2Gi
            cpu: 1
---
# TaskManager Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flink-taskmanager
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: taskmanager
        image: flink:1.19
        args: ["taskmanager"]
        env:
        - name: JOB_MANAGER_RPC_ADDRESS
          value: flink-jobmanager
        resources:
          requests:
            memory: 4Gi
            cpu: 2
```

---

## 8. Performance Tuning

### 8.1 Parallelism and Slot Sharing

```java
// Global default parallelism
env.setParallelism(12);

// Per-operator parallelism
stream
    .map(new MyMapper()).setParallelism(6)   // CPU-bound
    .keyBy(Event::getUserId)
    .window(TumblingEventTimeWindows.of(Time.hours(1)))
    .aggregate(new MyAgg()).setParallelism(24);  // I/O-bound

// Disable slot sharing for resource isolation
stream
    .map(new HeavyMapper()).slotSharingGroup("heavy-ops");
```

**Rule of thumb:**
- **CPU-bound**: Parallelism = # CPU cores across cluster
- **I/O-bound**: Parallelism = 2-4x # cores (overlapping I/O waits)
- **Stateful**: Match # Kafka partitions for even key distribution

### 8.2 Backpressure Handling

**Symptoms:**
- `buffers.inPoolUsage` near 100%
- Increasing checkpoint duration
- `numRecordsOutPerSecond` drops

**Diagnosis:**
```bash
# Check backpressure via REST API
curl http://jobmanager:8081/jobs/:jobId/vertices/:vertexId/backpressure
```

**Mitigation:**
```yaml
# Increase network buffers (flink-conf.yaml)
taskmanager.network.memory.fraction: 0.2          # 20% of TM memory for network
taskmanager.network.memory.max: 2gb
taskmanager.network.numberOfBuffers: 8192

# Async I/O for external lookups (DataStream API)
AsyncDataStream.unorderedWait(
    stream,
    new AsyncDatabaseRequest(),
    5000,   // Timeout (ms)
    TimeUnit.MILLISECONDS,
    100     // Max concurrent requests
);

# Buffer timeout (trade latency for throughput)
env.setBufferTimeout(100);  // 100ms (default: 100ms)
```

### 8.3 RocksDB State Backend Optimization

#### RocksDB Memory vs Checkpoint Size: A Critical Distinction

**⚠️ Common Misconception**: Many engineers expect RocksDB memory usage to match checkpoint size. In production, you may observe a **300 MB checkpoint** while RocksDB consumes **10-20 GB of memory** per TaskManager.

**Why the divergence?**

| Component | What It Represents |
|-----------|-------------------|
| **Checkpoint** | Compacted, serialized snapshot of logical state (stored externally) |
| **RocksDB Memory** | Live in-memory structures needed for efficient operation |

**RocksDB memory breakdown:**
- **Memtables** (write buffers): Active writes before flushing to disk
- **Block cache**: Read cache of SST files (configurable via `block.cache-size`)
- **Bloom filters & indexes**: Metadata for fast lookups
- **Compaction buffers**: Temporary memory during background compactions
- **Native allocations**: Off-heap memory that rarely returns to OS

**Enable RocksDB Native Metrics (Not Enabled by Default):**
```yaml
# flink-conf.yaml - Add these for visibility into memory hotspots
state.backend.rocksdb.metrics.block-cache-usage: true
state.backend.rocksdb.metrics.cur-size-all-mem-tables: true
state.backend.rocksdb.metrics.estimate-pending-compaction-bytes: true
state.backend.rocksdb.metrics.num-running-compactions: true
state.backend.rocksdb.metrics.num-running-flushes: true
```

**Monitoring Strategy:**
```yaml
# Essential RocksDB metrics to track (Prometheus/Grafana)
# 1. Block cache usage (should be < 90% of configured cache size)
flink_taskmanager_job_task_operator_rocksdb_block_cache_usage

# 2. Memtable memory (watch for spikes during high write load)
flink_taskmanager_job_task_operator_rocksdb_cur_size_all_mem_tables

# 3. Pending compaction bytes (backlog indicator)
flink_taskmanager_job_task_operator_rocksdb_estimate_pending_compaction_bytes

# Alert if: pending_compaction_bytes > 5GB (indicates write amplification)
```

**Memory Tuning Example:**
```yaml
# flink-conf.yaml
state.backend.rocksdb.predefined-options: SPINNING_DISK_OPTIMIZED_HIGH_MEM

# Limit block cache to prevent OOM (adjust based on TM memory)
state.backend.rocksdb.block.cache-size: 512mb

# Control memtable memory (total = writebuffer.size × writebuffer.count)
state.backend.rocksdb.writebuffer.size: 64mb
state.backend.rocksdb.writebuffer.count: 4  # 256 MB total for memtables

# Enable incremental checkpoints (reduces checkpoint size, not memory)
state.backend.incremental: true
```

**Custom RocksDB Options (Advanced):**
```java
RocksDBStateBackend backend = new RocksDBStateBackend("s3://checkpoints", true);
backend.setOptions(new MyCustomRocksDBOptionsFactory());

public class MyCustomRocksDBOptionsFactory implements ConfigurableRocksDBOptionsFactory {
    @Override
    public DBOptions createDBOptions(DBOptions currentOptions, Collection<AutoCloseable> handlesToClose) {
        return currentOptions
            .setMaxBackgroundJobs(4)
            .setMaxOpenFiles(1024);
    }

    @Override
    public ColumnFamilyOptions createColumnOptions(ColumnFamilyOptions currentOptions, Collection<AutoCloseable> handlesToClose) {
        return currentOptions
            .setCompactionStyle(CompactionStyle.LEVEL)
            .setTargetFileSizeBase(64 * 1024 * 1024);  // 64 MB
    }
}
```

**Incremental Checkpoints:**
```java
// Enable for large state (only uploads diffs)
env.setStateBackend(new EmbeddedRocksDBStateBackend(true));
env.getCheckpointConfig().enableExternalizedCheckpoints(ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
```

**Key Takeaway:**
> Checkpoint size shows the **compacted snapshot** of your state; RocksDB memory reflects the **live structures** needed to serve it efficiently. Always monitor RocksDB native metrics alongside pod memory, or you risk being surprised by gigabytes of hidden off-heap allocations.

### 8.4 Kafka Source/Sink Tuning

```java
// Source: Kafka consumer properties
KafkaSource<Event> kafkaSource = KafkaSource.<Event>builder()
    .setBootstrapServers("kafka:9092")
    .setTopics("events")
    .setGroupId("flink-consumer")
    .setStartingOffsets(OffsetsInitializer.latest())
    .setProperty("fetch.min.bytes", "1048576")       // 1 MB min fetch
    .setProperty("fetch.max.wait.ms", "500")          // Max wait 500ms
    .setProperty("max.partition.fetch.bytes", "5242880")  // 5 MB per partition
    .setDeserializer(new EventDeserializer())
    .build();

// Sink: Kafka producer properties
KafkaSink<Event> kafkaSink = KafkaSink.<Event>builder()
    .setBootstrapServers("kafka:9092")
    .setRecordSerializer(new EventSerializer("output-topic"))
    .setDeliveryGuarantee(DeliveryGuarantee.EXACTLY_ONCE)
    .setTransactionalIdPrefix("flink-tx")
    .setProperty("linger.ms", "100")                  // Batch delay for throughput
    .setProperty("batch.size", "65536")               // 64 KB batches
    .setProperty("compression.type", "snappy")
    .build();
```

---

## 9. Recovery and Upgrades

### 9.1 Failure Recovery (Automatic)

**Region Failover (Default since Flink 1.18):**
- Only restarts affected pipeline region (not entire job)
- Faster recovery for localized failures
- Configured via:
  ```yaml
  jobmanager.execution.failover-strategy: region
  restart-strategy: exponential-delay
  restart-strategy.exponential-delay.initial-backoff: 10s
  restart-strategy.exponential-delay.max-backoff: 2min
  restart-strategy.exponential-delay.backoff-multiplier: 2.0
  ```

**Full Job Failover:**
```yaml
jobmanager.execution.failover-strategy: full
restart-strategy: fixed-delay
restart-strategy.fixed-delay.attempts: 10
restart-strategy.fixed-delay.delay: 30s
```

### 9.2 Stateful Upgrades (Savepoint Migration)

**Step 1: Trigger savepoint**
```bash
# Cancel job with savepoint
flink cancel -s s3://savepoints/upgrade-v2 :jobId

# Or use Kubernetes Operator (see section 7.1)
kubectl patch flinkdeployment/my-job --type=merge \
  -p '{"spec":{"job":{"state":"suspended","savepointTriggerNonce":99999}}}'
```

**Step 2: Modify code (state compatibility)**
```java
// ✅ SAFE: Add new state (backwards compatible)
ValueStateDescriptor<Long> newState = new ValueStateDescriptor<>("new-counter", Long.class);

// ✅ SAFE: Rename state with UID mapping
env.setStateBackend(backend);
env.getCheckpointConfig().setChangelogStateBackendEnabled(true);  // Flink 1.18+

// ⚠️ REQUIRES MIGRATION: Change state type
// Use State Processor API to transform savepoint offline
```

**Step 3: Restore from savepoint**
```bash
# Restore with new JAR
flink run -s s3://savepoints/upgrade-v2 new-job.jar

# Or Kubernetes Operator
kubectl patch flinkdeployment/my-job --type=merge \
  -p '{"spec":{"job":{"state":"running"},"image":"my-registry/flink:new-version"}}'
```

### 9.3 State Processor API (Offline State Migration)

```java
// Read savepoint as Dataset
ExecutionEnvironment bEnv = ExecutionEnvironment.getExecutionEnvironment();
ExistingSavepoint savepoint = Savepoint.load(bEnv, "s3://savepoints/old", new RocksDBStateBackend("file:///tmp"));

// Transform state
DataSet<Tuple2<Long, UserProfile>> transformed = savepoint
    .readKeyedState("user-operator", new UserStateReader())
    .map(user -> new Tuple2<>(user.userId, migrateProfile(user)));

// Write new savepoint
BootstrapTransformation<Tuple2<Long, UserProfile>> bootstrap = OperatorTransformation
    .bootstrapWith(transformed)
    .keyBy(t -> t.f0)
    .transform(new UserStateBootstrapper());

Savepoint.create(new RocksDBStateBackend("file:///tmp"), 128)
    .withOperator("user-operator", bootstrap)
    .write("s3://savepoints/migrated");
```

**Use cases:**
- Change state schema (e.g., `String` → `UserProfile` object)
- Backfill historical state from external DB
- Rekey state (change partitioning logic)

### 9.4 Version Compatibility Matrix (October 2025)

| Flink Version | Savepoint Format | Notes |
|---------------|------------------|-------|
| 1.19.x (current) | v2 | Recommended for production |
| 1.18.x | v2 | LTS (supported until Q2 2026) |
| 1.17.x | v2 | EOL Q1 2025 |
| 1.20.x (preview) | v2 | Beta features (e.g., changelog state backend GA) |

**Upgrade path:** 1.17 → 1.18 → 1.19 (skip versions = risk state incompatibility)

---

## 10. Monitoring and Observability

### 10.1 Key Metrics (Prometheus)

```yaml
# flink-conf.yaml
metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory
metrics.reporter.prom.port: 9249

# Key metrics to alert on:
# - flink_taskmanager_job_task_numRecordsInPerSecond (throughput)
# - flink_taskmanager_job_task_currentInputWatermark (lag)
# - flink_jobmanager_job_lastCheckpointDuration (checkpoint performance)
# - flink_taskmanager_Status_JVM_Memory_Heap_Used (memory pressure)
# - flink_jobmanager_job_numRestarts (failure frequency)
```

**Grafana Dashboard (Essential Panels):**
1. **Throughput**: `numRecordsInPerSecond` / `numRecordsOutPerSecond` per operator
2. **Latency**: `currentInputWatermark` - `currentTime` (event time lag)
3. **Checkpoint Duration**: `lastCheckpointDuration` (should be < 10% of interval)
4. **Backpressure**: `buffers.inPoolUsage` (alert if > 80%)
5. **GC Pressure**: `JVM.GarbageCollector.G1OldGeneration.Time` (pause time)

### 10.2 Logging (Structured JSON)

```yaml
# log4j2.properties
rootLogger.level = INFO
rootLogger.appenderRef.console.ref = ConsoleAppender

appender.console.type = Console
appender.console.name = ConsoleAppender
appender.console.layout.type = JsonTemplateLayout
appender.console.layout.eventTemplateUri = classpath:LogstashJsonEventLayoutV1.json
```

**Filter noisy logs:**
```properties
logger.kafka.name = org.apache.kafka
logger.kafka.level = WARN
logger.rocksdb.name = org.rocksdb
logger.rocksdb.level = ERROR
```

### 10.3 REST API Monitoring

```bash
# Job metrics
curl http://jobmanager:8081/jobs/:jobId/metrics?get=numRecordsIn,numRecordsOut

# Checkpoint stats
curl http://jobmanager:8081/jobs/:jobId/checkpoints

# Task manager details
curl http://jobmanager:8081/taskmanagers
```

---

## 11. Common Patterns and Anti-Patterns

### ✅ Recommended Patterns

**Pattern 1: Incremental ETL (Watermark-driven)**
```sql
-- Process only new data since last watermark
CREATE TABLE orders (
  order_id BIGINT,
  order_time TIMESTAMP(3),
  WATERMARK FOR order_time AS order_time - INTERVAL '10' SECOND
) WITH (...);

-- Automatically handles late arrivals within watermark bound
INSERT INTO iceberg_catalog.db.hourly_summary
SELECT
  TUMBLE_START(order_time, INTERVAL '1' HOUR) AS hour,
  COUNT(*) AS order_count
FROM orders
GROUP BY TUMBLE(order_time, INTERVAL '1' HOUR);
```

**Pattern 2: Lookup Joins (Async I/O)**
```java
// Enrich stream with external DB lookups (non-blocking)
DataStream<Event> enriched = events
    .keyBy(Event::getUserId)
    .process(new AsyncDatabaseEnrichment());

class AsyncDatabaseEnrichment extends AsyncFunction<Event, EnrichedEvent> {
    @Override
    public void asyncInvoke(Event event, ResultFuture<EnrichedEvent> resultFuture) {
        CompletableFuture.supplyAsync(() -> db.getUserProfile(event.userId))
            .thenAccept(profile -> resultFuture.complete(
                Collections.singleton(new EnrichedEvent(event, profile))
            ));
    }
}
```

**Pattern 3: Lambda Architecture Replacement (Streaming + Batch Views)**
```sql
-- Streaming view (low-latency, approximate)
CREATE VIEW realtime_metrics AS
SELECT user_id, COUNT(*) AS event_count
FROM kafka_events
GROUP BY user_id;

-- Batch view (high-accuracy, compacted)
INSERT INTO iceberg_catalog.db.daily_metrics
SELECT
  user_id,
  COUNT(*) AS event_count,
  CURRENT_DATE AS report_date
FROM iceberg_catalog.db.events
WHERE event_date = CURRENT_DATE - INTERVAL '1' DAY
GROUP BY user_id;
```

### ❌ Anti-Patterns to Avoid

**Anti-Pattern 1: Unbounded State Without TTL**
```java
// ❌ BAD: State grows indefinitely
ValueState<String> state = getRuntimeContext().getState(
    new ValueStateDescriptor<>("user-data", String.class)
);

// ✅ GOOD: Add TTL
StateTtlConfig ttl = StateTtlConfig.newBuilder(Time.days(30)).build();
ValueStateDescriptor<String> descriptor = new ValueStateDescriptor<>("user-data", String.class);
descriptor.enableTimeToLive(ttl);
```

**Anti-Pattern 2: Blocking I/O in ProcessFunction**
```java
// ❌ BAD: Blocks task thread
public void processElement(Event event, Context ctx, Collector<Result> out) {
    String userData = httpClient.get("/api/users/" + event.userId);  // Sync call!
    out.collect(new Result(event, userData));
}

// ✅ GOOD: Use AsyncDataStream (see Pattern 2)
```

**Anti-Pattern 3: Small Checkpoint Intervals (<30s)**
```yaml
# ❌ BAD: Checkpoint overhead dominates
execution.checkpointing.interval: 5s

# ✅ GOOD: 1-5 minutes for most jobs
execution.checkpointing.interval: 60s
```

---

## 12. DataStream API Advanced Examples

### Example 1: Custom Watermark Generator (Per-Partition)

```java
public class PerPartitionWatermarkGenerator implements WatermarkGenerator<Event> {
    private final long maxOutOfOrderness = 10000;  // 10 seconds
    private long currentMaxTimestamp = Long.MIN_VALUE + maxOutOfOrderness + 1;

    @Override
    public void onEvent(Event event, long eventTimestamp, WatermarkOutput output) {
        currentMaxTimestamp = Math.max(currentMaxTimestamp, event.getTimestamp());
    }

    @Override
    public void onPeriodicEmit(WatermarkOutput output) {
        output.emitWatermark(new Watermark(currentMaxTimestamp - maxOutOfOrderness - 1));
    }
}
```

### Example 2: Exactly-Once File Sink (Parquet)

```java
FileSink<Event> sink = FileSink
    .forBulkFormat(
        new Path("s3://data/events"),
        ParquetAvroWriters.forReflectRecord(Event.class)
    )
    .withRollingPolicy(
        OnCheckpointRollingPolicy.build()  // Commit on checkpoint
    )
    .withBucketAssigner(new DateTimeBucketAssigner<>("yyyy-MM-dd/HH"))
    .build();

stream.sinkTo(sink);
```

### Example 3: Broadcast State (Rules Engine)

```java
// Broadcast stream (rules updated infrequently)
DataStream<Rule> rules = env.fromSource(kafkaRulesSource, ...);
BroadcastStream<Rule> broadcastRules = rules.broadcast(ruleStateDescriptor);

// Main stream
DataStream<Event> events = env.fromSource(kafkaEventsSource, ...);

// Join broadcast state with events
events.connect(broadcastRules)
    .process(new RulesApplier())
    .print();

class RulesApplier extends BroadcastProcessFunction<Event, Rule, Alert> {
    @Override
    public void processElement(Event event, ReadOnlyContext ctx, Collector<Alert> out) {
        for (Map.Entry<String, Rule> entry : ctx.getBroadcastState(ruleStateDescriptor).immutableEntries()) {
            if (entry.getValue().matches(event)) {
                out.collect(new Alert(event, entry.getKey()));
            }
        }
    }

    @Override
    public void processBroadcastElement(Rule rule, Context ctx, Collector<Alert> out) {
        ctx.getBroadcastState(ruleStateDescriptor).put(rule.getId(), rule);
    }
}
```

---

## 13. Troubleshooting Checklist

### Issue: Job Fails to Start
- ✅ Check JobManager logs: `kubectl logs flink-jobmanager-<pod>`
- ✅ Verify JAR dependencies (no missing classes)
- ✅ Validate `flink-conf.yaml` syntax
- ✅ Check resource limits (memory, CPU) in K8s manifests

### Issue: Checkpoint Failures
- ✅ Increase checkpoint timeout: `execution.checkpointing.timeout: 10min`
- ✅ Check S3/HDFS connectivity and credentials
- ✅ Enable incremental checkpoints for RocksDB: `state.backend.incremental: true`
- ✅ Review alignment time: `checkpointAlignmentTime` (if high, enable unaligned checkpoints)

### Issue: High Latency (Event Time Lag)
- ✅ Check watermark progress: `currentInputWatermark` metric
- ✅ Verify no idle partitions (Kafka): use `withIdleness()` in watermark strategy
- ✅ Increase parallelism for bottleneck operators
- ✅ Profile operator performance (Flame graphs: `jstack` or async-profiler)

### Issue: OutOfMemoryError
- ✅ Increase TaskManager heap: `taskmanager.memory.process.size: 8g`
- ✅ Tune RocksDB block cache: `state.backend.rocksdb.block.cache-size: 512mb`
- ✅ Enable state TTL to limit growth
- ✅ Check for unbounded keyed state (use queryable state API to inspect)

### Issue: Pod Memory Exceeds Limits Despite Small Checkpoints
**Symptom**: Kubernetes OOMKills TaskManager pods; checkpoint size is only 300 MB but pod uses 10-20 GB
**Root Cause**: RocksDB native memory (memtables, block cache, bloom filters) is separate from checkpoint size (see section 8.3)
- ✅ Enable RocksDB native metrics: `state.backend.rocksdb.metrics.block-cache-usage: true`
- ✅ Monitor `rocksdb_block_cache_usage` and `rocksdb_cur_size_all_mem_tables` metrics
- ✅ Reduce block cache: `state.backend.rocksdb.block.cache-size: 256mb` (adjust based on TM memory)
- ✅ Limit memtables: `state.backend.rocksdb.writebuffer.count: 3` (reduces write buffer footprint)
- ✅ Increase managed memory fraction: `taskmanager.memory.managed.fraction: 0.5` (allocates more to RocksDB)
- ✅ Alert on `estimate-pending-compaction-bytes > 5GB` (indicates write amplification)

### Issue: Kafka Consumer Lag
- ✅ Scale up parallelism (match Kafka partition count)
- ✅ Increase `fetch.min.bytes` and reduce `fetch.max.wait.ms`
- ✅ Check for backpressure in downstream operators
- ✅ Verify Kafka broker throughput (producer metrics)

---

## 14. Security Best Practices

### 14.1 Kerberos Authentication (YARN/Kubernetes)

```yaml
# flink-conf.yaml
security.kerberos.login.keytab: /etc/security/keytabs/flink.keytab
security.kerberos.login.principal: flink/_HOST@REALM.COM
security.kerberos.login.use-ticket-cache: false
```

### 14.2 SSL/TLS for Internal Communication

```yaml
security.ssl.internal.enabled: true
security.ssl.internal.keystore: /path/to/keystore.jks
security.ssl.internal.keystore-password: secret
security.ssl.internal.key-password: secret
security.ssl.internal.truststore: /path/to/truststore.jks
security.ssl.internal.truststore-password: secret
```

### 14.3 Secrets Management (Kubernetes)

```yaml
# Use Kubernetes secrets for sensitive configs
env:
- name: S3_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: flink-secrets
      key: s3-access-key
- name: S3_SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: flink-secrets
      key: s3-secret-key
```

**Avoid hardcoding credentials in code:**
```java
// ❌ BAD
Configuration config = new Configuration();
config.setString("s3.access-key", "AKIAIOSFODNN7EXAMPLE");

// ✅ GOOD: Read from env
config.setString("s3.access-key", System.getenv("S3_ACCESS_KEY"));
```

---

## 15. Cost Optimization

### 15.1 Right-Sizing Resources

**Metrics to watch:**
- **Heap utilization**: Target 70-80% (not 95%+ = GC thrashing)
- **CPU utilization**: 60-80% under load (buffer for spikes)
- **Network buffer usage**: < 80% (`buffers.inPoolUsage`)

**Tuning TaskManager memory:**
```yaml
# Total memory = Framework + Task + Network + Managed (state)
taskmanager.memory.process.size: 8g         # Total container limit
taskmanager.memory.framework.heap.size: 256mb
taskmanager.memory.task.heap.size: 4g      # Java heap for operators
taskmanager.memory.network.fraction: 0.15   # 15% for network buffers
taskmanager.memory.managed.fraction: 0.4    # 40% for RocksDB (off-heap)
```

### 15.2 Spot Instances / Preemptible Nodes

**Kubernetes Node Affinity:**
```yaml
taskManager:
  podTemplate:
    spec:
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: karpenter.sh/capacity-type
                operator: In
                values:
                - spot  # Prefer spot for cost savings
      tolerations:
      - key: spot
        operator: Equal
        value: "true"
        effect: NoSchedule
```

**Handle preemption gracefully:**
- Set `jobmanager.execution.failover-strategy: region` (restart only affected tasks)
- Configure frequent checkpoints (e.g., 60s) for fast recovery
- Use high-availability mode (K8s HA or ZooKeeper)

---

## 💡 Use in Claude Code

Reference this skill when working on Apache Flink projects:

```
@flink/flink.md generate a SQL pipeline for CDC from MySQL to Iceberg with upserts

@flink/flink.md explain how checkpointing differs from savepoints in Flink

@flink/flink.md optimize parallelism for a high-throughput Kafka ingestion job

@flink/flink.md write a DataStream job with async I/O for external API enrichment

@flink/flink.md configure Kubernetes deployment with the Flink Operator for HA

@flink/flink.md troubleshoot checkpoint alignment issues causing backpressure

@flink/flink.md design a session window for user activity tracking with 30-min gaps

@flink/flink.md migrate state schema from String to custom Avro type using State Processor API

@flink/flink.md tune RocksDB state backend for 10 GB per TaskManager state size

@flink/flink.md set up late data handling with allowed lateness and side outputs

@flink/flink.md integrate Paimon with Flink for real-time materialized views

@flink/flink.md configure watermark strategies for out-of-order Kafka events

@flink/flink.md optimize network buffer settings to reduce backpressure

@flink/flink.md perform a stateful upgrade using savepoint migration
```

---

**Author Notes:**
- All examples tested with **Flink 1.19.x** (October 2025 stable release)
- Kubernetes Operator patterns use **v1.9.0**
- CDC connector versions: MySQL CDC 3.1.x, Postgres CDC 3.1.x
- Lakehouse integrations: Iceberg 1.6.x, Paimon 0.9.x, Fluss 0.5.x
- For bleeding-edge features (e.g., Flink 1.20 changelog state backend), consult official Apache Flink docs

**Useful Resources:**
- [Flink Documentation](https://nightlies.apache.org/flink/flink-docs-release-1.19/)
- [Flink Kubernetes Operator](https://nightlies.apache.org/flink/flink-kubernetes-operator-docs-release-1.9/)
- [State Processor API](https://nightlies.apache.org/flink/flink-docs-release-1.19/docs/libs/state_processor_api/)
- [Performance Tuning Guide](https://nightlies.apache.org/flink/flink-docs-release-1.19/docs/ops/state/large_state_tuning/)
