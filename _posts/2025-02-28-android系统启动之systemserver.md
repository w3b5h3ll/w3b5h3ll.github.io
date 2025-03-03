---
layout: post
title: "Android系统启动之SystemServer"
date: 2025-02-28 14:13:55
tags: Android
---

`SystemServer` 是 Android 系统的核心进程，负责启动和管理系统服务。本文基于 [SystemServer.java](https://github.com/aosp-mirror/platform_frameworks_base/blob/main/services/java/com/android/server/SystemServer.java) 源码，分析其执行流程、服务分类及运行机制。（基于 Android 10 版本）

**在线阅读地址**：

- [XRefAndroid - Support AOSP 15.0 AndroidXRef & OpenHarmony 5.0](https://xrefandroid.com/)
- [Cross Reference: /frameworks/base/services/java/com/android/server/SystemServer.java](http://androidxref.com/9.0.0_r3/xref/frameworks/base/services/java/com/android/server/SystemServer.java)

## 构造函数

```java
public SystemServer() {
    // 检查工厂测试模式
    mFactoryTestMode = FactoryTest.getMode();

    // 记录进程启动信息
    // 注意：在 FDE 设备上，SYSPROP_START_COUNT 会递增 2 次：一次用于密码屏幕，一次用于实际启动
    mStartCount = SystemProperties.getInt(SYSPROP_START_COUNT, 0) + 1;
    mRuntimeStartElapsedTime = SystemClock.elapsedRealtime();
    mRuntimeStartUptime = SystemClock.uptimeMillis();

    // 判断是否为运行时重启（当 sys.boot_completed 已设置时）
    // 注意：如果进程在 sys.boot_completed 设置之前崩溃，mRuntimeRestart 不会被正确设置为 true
    mRuntimeRestart = "1".equals(SystemProperties.get("sys.boot_completed"));
}
```

| **功能**         | **实现方式**                                                 | **作用**                               |
| :--------------- | :----------------------------------------------------------- | :------------------------------------- |
| 工厂测试模式检查 | 调用 `FactoryTest.getMode()` 获取当前模式。                  | 影响系统服务的启动行为。               |
| 启动信息记录     | 读取系统属性 `SYSPROP_START_COUNT`，记录启动时间和单调时间。 | 用于统计和分析系统启动行为。           |
| 运行时重启判断   | 检查系统属性 `sys.boot_completed` 是否为 `"1"`。             | 区分冷启动和运行时重启，优化启动流程。 |

通过构造函数，`SystemServer` 完成了系统状态的初始化和关键变量的设置，为后续的系统服务启动提供了必要的上下文信息。

---

## 启动入口：`main()` 与 `run()` 方法

```java
public static void main(String[] args) {
    new SystemServer().run();
}
// ...
private void run() {
    // 1. 初始化前阶段
    InitBeforeStartServices();
    // 2. 创建系统上下文
    createSystemContext();
    // 3. 启动服务阶段
    startBootstrapServices();  // 引导服务
    startCoreServices();       // 核心服务
    startOtherServices();      // 其他服务
    // 4. 进入事件循环
    Looper.loop();
}

```

## 初始化前阶段 (`InitBeforeStartServices`)

### 基础环境准备

| **步骤**             | **代码实现**                                                       | **作用**                              |
| :------------------- | :----------------------------------------------------------------- | :------------------------------------ |
| 系统属性设置         | `SystemProperties.set()`                                           | 配置全局属性（如启动次数、时间戳）    |
| 时区/语言初始化      | `TimezoneDetectorService.initialize()` `LocalePicker.initialize()` | 加载默认时区和语言设置                |
| Binder 初始化        | `BinderInternal.disableBackgroundScheduling()`                     | 配置 Binder 线程池参数                |
| 主线程 Looper 初始化 | `Looper.prepareMainLooper()`                                       | 创建主线程消息循环                    |
| 本地库加载           | `System.loadLibrary("android_servers")`                            | 加载系统服务所需的本地库（如 Binder） |

### 系统上下文创建 (`createSystemContext`)

```java
private void createSystemContext() {
    ActivityThread activityThread = ActivityThread.systemMain();
    mSystemContext = activityThread.getSystemContext();
    mSystemContext.setTheme(DEFAULT_SYSTEM_THEME);
}
```

- **作用**：创建系统级的 `Context` 和主题，为服务提供运行环境。

---

## 服务启动阶段 (`StartServices`)

引导服务 (`startBootstrapServices`)

| **服务**               | **代码调用**                                                    | **功能**                    |
| :--------------------- | :-------------------------------------------------------------- | :-------------------------- |
| Watchdog               | `Watchdog.getInstance().start()`                                | 监控系统服务健康状态        |
| Installer              | `mSystemServiceManager.startService(Installer.class)`           | 应用安装的底层操作          |
| ActivityManagerService | `ActivityManagerService.Lifecycle.startService(...)`            | 管理四大组件生命周期        |
| PowerManagerService    | `mSystemServiceManager.startService(PowerManagerService.class)` | 电源状态管理（如亮屏/熄屏） |

- **依赖关系**：
  - `ActivityManagerService` 依赖 `Installer` 完成应用安装。
  - `PowerManagerService` 必须优先启动，供其他服务调用电源锁。

核心服务 (`startCoreServices`)

| **服务**             | **代码调用**                                                     | **功能**              |
| :------------------- | :--------------------------------------------------------------- | :-------------------- |
| BatteryService       | `mSystemServiceManager.startService(BatteryService.class)`       | 电池状态监控          |
| WebViewUpdateService | `mSystemServiceManager.startService(WebViewUpdateService.class)` | 管理 WebView 组件更新 |

其他服务 (`startOtherServices`)

| **服务类型** | **示例服务**               | **代码调用**                                                   |
| :----------- | :------------------------- | :------------------------------------------------------------- |
| 输入管理     | `InputManagerService`      | `inputManager = new InputManagerService(context)`              |
| 窗口管理     | `WindowManagerService`     | `wm = WindowManagerService.main(...)`                          |
| 网络管理     | `NetworkManagementService` | `networkManagement = NetworkManagementService.create(context)` |

APEX 服务 (`startApexServices`)

```java
private void startApexServices() {
    ApexManager apexManager = ApexManager.getInstance();
    List<ActiveApexInfo> apexes = apexManager.getActiveApexInfos();
    // 动态加载 APEX 包中的服务
}
```

---

## 系统准备阶段 (`systemReady`)

通知系统就绪

```java
mActivityManagerService.systemReady(() -> {
    // 启动 SystemUI、网络服务等
    startSystemUi(context);
    mNetworkManagementService.systemReady();
});
```

- **作用**：通知 `ActivityManagerService` 系统已就绪，启动第三方应用。

关键操作

- **网络堆栈初始化**：`NetworkStackClient.getInstance().start(context)`
- **飞行模式设置**：根据安全模式状态启用或禁用。

---

## 进入事件循环 (`Looper.loop()`)

主线程进入消息循环

```java
Looper.loop();  // 进入无限循环，处理 Binder 消息和事件
```

- **作用**：系统服务启动完成后，主线程通过 `Looper` 处理异步任务和跨进程通信。

消息处理机制

- **Binder 通信**：通过 `Binder` 线程池接收请求，转发到主线程处理。
- **Handler 分发**：服务通过注册 `Handler` 处理异步任务（如电源键事件）。

---

## 关键设计解析

### 服务启动顺序优化

- **分阶段启动**：
  - **引导服务**（`PHASE_WAIT_FOR_DEFAULT_DISPLAY`）：依赖显示设备初始化。
  - **核心服务**（`PHASE_SYSTEM_SERVICES_READY`）：启动电池、统计等基础功能。
  - **其他服务**（`PHASE_THIRD_PARTY_APPS_CAN_START`）：允许第三方应用启动。

### 依赖管理

- **SystemServiceManager**：通过 `startService()` 和 `startBootPhase()` 管理服务生命周期。

```java
mSystemServiceManager.startService(Installer.class);
mSystemServiceManager.startBootPhase(SystemService.PHASE_BOOT_COMPLETED);
```

### 异常处理

- **日志与崩溃**：通过 `Slog.e()` 记录错误，`reportWtf()` 抛出严重异常。

```java
try {
    startBootstrapServices();
} catch (Throwable ex) {
    Slog.e("System", "Failure starting system services", ex);
    throw ex;
}
```

---

## SystemServer启动总结

| **阶段**     | **关键操作**                     | **依赖关系**                   |
| :----------- | :------------------------------- | :----------------------------- |
| **初始化前** | 系统属性、Binder、Looper 初始化  | 无                             |
| **引导服务** | 启动 Watchdog、AMS、PowerManager | Installer → AMS → PowerManager |
| **核心服务** | 启动电池、WebView 更新           | 依赖引导服务完成               |
| **其他服务** | 启动窗口管理、网络服务           | 依赖核心服务和引导服务         |
| **系统就绪** | 通知 AMS、启动第三方应用         | 所有服务启动完成               |

通过分阶段启动和严格依赖管理，`SystemServer` 确保 Android 系统高效稳定运行。深入理解其源码，对优化系统启动速度和排查服务初始化问题具有重要意义。

---

## 线程

| **线程类型**      | **关键操作**                                           | **作用**                                                     |
| :---------------- | :----------------------------------------------------- | :----------------------------------------------------------- |
| **主线程**        | `Looper.prepareMainLooper()`、`Looper.loop()`          | 处理系统服务的消息循环，确保异步任务和事件能够及时处理。     |
| **后台线程池**    | `SystemServerInitThreadPool.get()`、`submit()`         | 并行执行系统服务的初始化任务，加速启动过程。                 |
| **Binder 线程池** | `BinderInternal.setMaxThreads()`                       | 处理跨进程通信请求，确保 Binder 调用能够高效执行。           |
| **异步任务**      | `Future`、`ConcurrentUtils.waitForFutureNoInterrupt()` | 提交和等待异步任务，确保任务之间的依赖关系。                 |
| **线程优先级**    | `setThreadPriority()`、`setCanSelfBackground()`        | 确保主线程和 Binder 线程具有高优先级，避免被降级为后台线程。 |

### 服务启动方式

线程启动

```java
mSystemServiceManager.startService(ActivityManagerService.Lifecycle.class);
```

- **实现方式**：
  - 通过 `SystemServiceManager` 启动服务，服务运行在 `SystemServer` 的线程中。
  - 服务的 `onStart()` 方法会在 `SystemServer` 的主线程中执行。

进程

```
ServiceManager.addService("media", new MediaServer());
```

- **实现方式**：
  - 通过 `ServiceManager` 注册服务，服务运行在独立的进程中。
  - 服务的 `main()` 方法会在新进程中执行。

### 线程间通信

机制概述

- **线程间通信** 是指在同一进程内的不同线程之间传递消息或数据。
- 在 `SystemServer` 中，线程间通信主要通过 **`Handler` 和 `Looper`** 实现。

#### 关键代码分析

主线程的 `Looper` 初始化

```java
Looper.prepareMainLooper();
Looper.getMainLooper().setSlowLogThresholdMs(
    SLOW_DISPATCH_THRESHOLD_MS, SLOW_DELIVERY_THRESHOLD_MS);
```

- **作用**：
  - 为主线程初始化一个 `Looper` 对象，用于处理消息队列。
  - 设置消息处理的慢日志阈值，帮助开发者分析性能问题。

主线程的消息循环

```java
Looper.loop();
```

- **作用**：
  - 启动主线程的消息循环，不断从消息队列中取出消息并分发给对应的 `Handler` 处理。

使用 `Handler` 发送消息

```
Handler handler = new Handler(Looper.getMainLooper());
handler.post(() -> {
    // 在主线程中执行的任务
});
```

- **作用**：
  - 通过 `Handler` 将任务提交到主线程的消息队列中执行。
  - 适用于需要在主线程中更新 UI 或执行其他任务的场景。

线程池中的任务提交

```
mSensorServiceStart = SystemServerInitThreadPool.get().submit(() -> {
    startSensorService();
});
```

- **作用**：
  - 将 `startSensorService()` 任务提交到线程池中异步执行。
  - 使用 `Future` 对象跟踪任务的执行状态和结果。

#### 消息分发机制

通过 `Handler` 和 `Looper` 机制，Android 实现了高效的线程间通信，确保主线程能够及时处理 UI 更新和其他任务，同时避免了多线程并发问题。

| **组件**         | **作用**                                                       | **关键方法**                       |
| :--------------- | :------------------------------------------------------------- | :--------------------------------- |
| **Looper**       | 负责消息循环，从 `MessageQueue` 中取出消息并分发给 `Handler`。 | `prepare()`、`loop()`              |
| **Handler**      | 负责发送和处理消息，与 `Looper` 绑定。                         | `sendMessage()`、`handleMessage()` |
| **MessageQueue** | 存储待处理的消息，支持定时任务。                               | `next()`、`enqueueMessage()`       |
| **Message**      | 消息的载体，包含数据和任务。                                   | `what`、`obj`、`target`            |

通过 `Message.target` 字段，Android 的 `Handler` 和 `Looper` 机制能够精确地将消息分发给对应的 `Handler`，确保消息处理的正确性和高效性。

| **关键点**           | **说明**                                                                            |
| :------------------- | :---------------------------------------------------------------------------------- |
| **`Message.target`** | 每个 `Message` 都包含一个 `target` 字段，指向处理该消息的 `Handler`。               |
| **消息的绑定**       | 通过 `Handler.obtainMessage()` 或 `Handler.sendMessage()` 绑定 `Handler`。          |
| **消息的分发**       | `Looper` 根据 `Message.target` 找到对应的 `Handler` 并分发消息。                    |
| **多 Handler 场景**  | 多个 `Handler` 可以绑定到同一个 `Looper`，但每个消息只会由发送它的 `Handler` 处理。 |

## 实验：分析system_server中的线程

```bash
emulator64_arm64:/ # ps -ef|grep system_server
system         403   207 1 05:09:21 ?     00:04:43 system_server
root          7710  7691 0 11:37:19 /sbin/.magisk/pts/0 00:00:00 grep system_server

emulator64_arm64:/proc/403/task # for t in *; do echo Thread $t `grep Name: $t/status`; done
Thread 1067 Name: AdbDebuggingMan
Thread 1069 Name: Binder:403_8
Thread 1083 Name: Binder:403_9
Thread 1084 Name: Binder:403_A
Thread 1107 Name: LazyTaskWriterT
Thread 1109 Name: backup-0
Thread 1140 Name: Binder:403_B
Thread 1145 Name: Binder:403_C
Thread 1156 Name: Binder:403_D
Thread 1161 Name: Binder:403_E
Thread 1176 Name: Binder:403_F
Thread 1214 Name: queued-work-loo
Thread 1652 Name: AsyncQueryWorke
Thread 2502 Name: AudioTrack
Thread 2689 Name: Binder:403_10
```

Task:

在 Linux 系统中，每个进程都有一个 `/proc/[pid]/task` 目录，其中 `[pid]` 是进程的 ID。`task` 目录包含了该进程的所有线程信息，每个线程都有一个对应的子目录，子目录的名称是线程的 ID（TID）。

进行排序后，由此可以看到一个大致的启动顺序

```bash
emulator64_arm64:/proc/403/task # for t in *; do echo Thread $t `grep Name: $t/status`; done | awk '{print $2, $0}' | sort -n | cut -d' ' -f2-
Thread 403 Name: system_server
Thread 409 Name: Jit thread pool
Thread 410 Name: Runtime worker
Thread 411 Name: Runtime worker
Thread 412 Name: Runtime worker
Thread 413 Name: Runtime worker
Thread 414 Name: Signal Catcher
Thread 415 Name: HeapTaskDaemon
Thread 416 Name: ReferenceQueueD
Thread 417 Name: FinalizerDaemon
Thread 418 Name: FinalizerWatchd
Thread 419 Name: Binder:403_1
Thread 420 Name: Binder:403_2
Thread 421 Name: android.fg
Thread 422 Name: android.ui
Thread 423 Name: android.io
Thread 424 Name: android.display
Thread 425 Name: android.anim
Thread 426 Name: android.anim.lf
Thread 427 Name: watchdog
Thread 429 Name: android.bg
Thread 430 Name: ActivityManager
Thread 431 Name: ActivityManager
Thread 432 Name: ActivityManager
Thread 433 Name: Thread-2
Thread 434 Name: OomAdjuster
Thread 435 Name: batterystats-wo
Thread 438 Name: FileObserver
Thread 439 Name: CpuTracker
Thread 440 Name: PowerManagerSer
Thread 441 Name: HwBinder:403_1
Thread 442 Name: BatteryStats_wa
Thread 443 Name: PackageManager
Thread 444 Name: PackageManager
Thread 499 Name: PackageInstalle
Thread 502 Name: SensorEventAckR
Thread 503 Name: SensorService
Thread 504 Name: HealthServiceRe
Thread 506 Name: RollbackManager
Thread 507 Name: RollbackPackage
Thread 509 Name: AccountManagerS
Thread 510 Name: SettingsProvide
Thread 511 Name: AlarmManager
Thread 515 Name: InputDispatcher
Thread 516 Name: InputReader
Thread 517 Name: NetworkWatchlis
Thread 518 Name: StorageManagerS
Thread 521 Name: NetworkStats
Thread 522 Name: NetworkPolicy
Thread 523 Name: tworkPolicy.uid
Thread 524 Name: WifiService
Thread 525 Name: ClientModeImpl
Thread 526 Name: WifiP2pService
Thread 527 Name: WifiScanningSer
Thread 528 Name: ConnectivitySer
Thread 529 Name: roid.pacmanager
Thread 530 Name: NsdService
Thread 531 Name: mDnsConnector
Thread 532 Name: notification-sq
```
