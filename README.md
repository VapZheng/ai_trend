# 鱼盆模型趋势看板

一个基于 `Vue 3 + Vite + Element Plus + ECharts + Python` 的趋势看板，用于展示鱼盆模型的市场强弱状态，并支持真实数据抓取、`sqlite` 存储、自动轮询更新、板块轮动榜单配置和 `docker` 部署。

当前版本已包含以下能力：
- 真实数据写入 `sqlite`
- 主看板支持自动轮询更新
- 页面支持 `5 日 / 20 日` 双视图切换
- 新增独立“板块轮动”页面，支持自定义代码配置与明细查看
- 项目支持 `docker` 部署

## 功能

- 支持按代码或名称搜索指数
- 支持 YES / NO 状态筛选
- 支持按数据时间切换历史快照
- 支持按趋势强度、偏离率、涨幅、状态转变时间排序
- 支持选择多个指数对比偏离率走势
- 支持 `5 日 / 20 日` 趋势视图切换
- 支持独立“板块轮动”页面与大表榜单视图
- 支持维护板块/指数代码配置，并将配置持久化到 `sqlite`
- 支持查看板块/指数的历史明细清单
- 支持将趋势快照存入 `sqlite`

## 技术栈

- 前端：`Vue 3`、`Vite`、`TypeScript`、`Element Plus`、`ECharts`
- 后端：`Python 3.12` 标准库 `HTTP server`
- 数据库：`sqlite`
- 数据抓取：`httpx`

## 本地运行

```bash
npm install
python3 -m pip install -r requirements-data.txt
```

前端启动：

```bash
npm run dev
```

后端启动：

```bash
npm run dev:api
```

开发环境下前端通过 `Vite proxy` 访问 `http://127.0.0.1:8000`。

## 后端说明

当前项目后端是一个基于 Python 标准库 HTTP 服务的 `sqlite` 服务，负责抓取真实数据、保存快照、自动轮询主看板数据，并向前端提供趋势看板与板块轮动的 `API`。

后端启动命令：

```bash
python3 -m backend.app --host 0.0.0.0 --port 8000 --static-dir dist
```

如果希望只执行一次抓取并写入 `sqlite`，也可以使用：

```bash
python3 scripts/generate_real_trends.py
```

如果还要额外导出一份 JSON：

```bash
python3 scripts/generate_real_trends.py --export-json public/data/trends.json
```

## API

- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/sector-rotation`
- `POST /api/sector-rotation/refresh`
- `POST /api/sector-rotation/targets`
- `DELETE /api/sector-rotation/targets?code=...`

## 构建部署

```bash
npm run build
```

## Docker 部署

```bash
docker compose up --build
```

启动后访问：`http://localhost:8000`

`sqlite` 数据会持久化到 `docker` volume：`trend-data`

## 数据说明

- 趋势视图支持 `5 日 / 20 日` 两种均线临界值，默认主视图为 `20 日`
- 默认数据库路径：`data/trends.db`
- Docker 内数据库路径：`/app/data/trends.db`
- 后端入口：`backend/app.py`
- 真实数据脚本：`scripts/generate_real_trends.py`
- 依赖安装：`python3 -m pip install -r requirements-data.txt`
- 生成命令：`npm run generate:data`
- 主看板默认每 `10` 秒自动轮询一次
- 板块轮动代码配置保存在 `sector_rotation_targets` 表
- 当前脚本默认抓取的指数：`上证指数`、`深证成指`、`创业板指`、`沪深300`、`中证500`、`中证1000`、`中证2000`、`科创50`、`北证50`、`恒生指数`、`国企指数`
- 板块轮动默认预置：`电力`、`半导体`、`证券Ⅱ`、`银行Ⅱ`、`汽车整车`、`机器人`
- 主看板日线数据默认走东财接口；板块轮动中的指数日线使用腾讯指数源，板块日线使用同花顺板块历史源
- 最新趋势快照保存在 `sqlite`，前端通过 `/api/dashboard` 读取
- 板块轮动榜单快照保存在 `sqlite`，前端通过 `/api/sector-rotation` 读取

可选环境变量：

- `TREND_DB_PATH`：自定义 `sqlite` 文件路径
- `TREND_HOST`：自定义监听地址
- `TREND_PORT`：自定义监听端口
# ai_trend
