<script setup lang="ts">
import { computed, ref } from 'vue';
import SectorRotationConfigDialog from './SectorRotationConfigDialog.vue';
import SectorRotationDetailDrawer from './SectorRotationDetailDrawer.vue';
import SectorRotationTable from './SectorRotationTable.vue';
import { useSectorRotation } from '../composables/useSectorRotation';
import { formatPercent } from '../utils/formatters';

const {
  activeTrendView,
  activeTrendViewMeta,
  addTarget,
  dataset,
  detailVisible,
  errorMessage,
  handleTrendViewChange,
  isLoading,
  isRefreshing,
  isSavingConfig,
  items,
  lastRun,
  marketOverview,
  openDetail,
  refreshSectorRotation,
  removeTarget,
  selectedItem,
  selectedTarget,
  setSelectedCode,
  targets,
  trendViewOptions,
} = useSectorRotation();

const isConfigVisible = ref(false);
const latestRunLabel = computed(() => lastRun.value?.finishedAt ?? lastRun.value?.startedAt ?? '--');
const latestDataDate = computed(() => dataset.value?.views[activeTrendView.value]?.latestDataDate ?? '--');
const strongestLabel = computed(() => {
  if (!marketOverview.value.strongestItem) {
    return '--';
  }
  return `${marketOverview.value.strongestItem.name} · ${marketOverview.value.strongestItem.code}`;
});

function handleViewDetail(item: (typeof items.value)[number]) {
  openDetail(item);
}
</script>

<template>
  <template v-if="isLoading">
    <el-skeleton :rows="8" animated />
  </template>

  <template v-else>
    <section class="hero-card rotation-hero">
      <div class="rotation-hero__main">
        <div>
          <p class="eyebrow">Sector Rotation · 板块轮动</p>
          <div class="rotation-hero__title">
            <h1>板块轮动</h1>
            <el-tag effect="dark" round size="large" type="primary">当前视图：{{ activeTrendViewMeta.label }}</el-tag>
          </div>
          <p class="hero-description">
            独立展示自定义板块/指数代码的轮动榜单。主榜单、概览结论和明细抽屉都跟随当前 {{ activeTrendViewMeta.label }} 视图联动。
          </p>
        </div>

        <div class="rotation-hero__toolbar">
          <el-segmented
            :model-value="activeTrendView"
            :options="trendViewOptions"
            class="rotation-hero__switch"
            size="large"
            @update:model-value="handleTrendViewChange"
          />

          <div class="rotation-hero__actions">
            <el-button plain size="large" @click="isConfigVisible = true">代码配置</el-button>
            <el-button :loading="isRefreshing" size="large" type="primary" @click="refreshSectorRotation">
              立即更新榜单
            </el-button>
          </div>
        </div>
      </div>

      <div class="rotation-hero__summary">
        <article class="hero-highlight">
          <span>已配置代码</span>
          <strong>{{ targets.length }}</strong>
          <p>当前配置会持久化到 sqlite，并用于后续板块轮动榜单抓取。</p>
        </article>
        <article class="hero-highlight">
          <span>{{ activeTrendViewMeta.shortLabel }} YES / NO</span>
          <strong>{{ `${marketOverview.yesCount} / ${marketOverview.noCount}` }}</strong>
          <p>{{ marketOverview.totalCount > 0 ? marketOverview.conclusionTitle : '完成榜单更新后展示状态分布。' }}</p>
        </article>
        <article class="hero-highlight">
          <span>平均偏离率</span>
          <strong>{{ marketOverview.totalCount > 0 ? formatPercent(marketOverview.averageDeviation) : '--' }}</strong>
          <p>{{ marketOverview.totalCount > 0 ? marketOverview.temperatureLabel : '等待榜单数据后展示整体温度。' }}</p>
        </article>
        <article class="hero-highlight">
          <span>最强对象</span>
          <strong>{{ strongestLabel }}</strong>
          <p>最新数据日 {{ latestDataDate }} · 最近执行 {{ latestRunLabel }}</p>
        </article>
      </div>
    </section>

    <el-alert v-if="errorMessage" :closable="false" :title="errorMessage" class="page-alert" type="error" />

    <section class="table-card rotation-table-card">
      <div class="table-head">
        <div>
          <h3>{{ activeTrendViewMeta.shortLabel }} 板块轮动榜</h3>
          <p>聚焦代码、名称、状态、涨幅、临界值、偏离率、状态时间与区间涨幅；点击行切换当前对象，点按钮查看历史明细。</p>
        </div>
        <div class="table-head__meta">
          <el-tag effect="plain" round size="large" type="primary">{{ activeTrendViewMeta.criticalLabel }}</el-tag>
          <el-tag effect="plain" round type="info">共 {{ items.length }} 条榜单</el-tag>
        </div>
      </div>

      <template v-if="dataset && items.length > 0">
        <SectorRotationTable
          :items="items"
          :selected-code="selectedItem?.code ?? ''"
          :trend-view="activeTrendViewMeta"
          @select="setSelectedCode($event.code)"
          @view-detail="handleViewDetail"
        />
      </template>

      <el-empty
        v-else-if="targets.length === 0"
        description="当前没有已配置代码，请先在“代码配置”里添加要跟踪的板块或指数。"
      />

      <el-empty
        v-else
        description="当前还没有生成榜单数据，点击右上角“立即更新榜单”开始抓取。"
      />
    </section>

    <SectorRotationConfigDialog
      v-model="isConfigVisible"
      :is-saving="isSavingConfig"
      :targets="targets"
      @add="addTarget"
      @remove="removeTarget"
    />

    <SectorRotationDetailDrawer
      v-model="detailVisible"
      :item="selectedItem"
      :target="selectedTarget"
      :trend-view="activeTrendViewMeta"
    />
  </template>
</template>

<style scoped>
.rotation-hero {
  display: grid;
  gap: 20px;
}

.rotation-hero__main,
.rotation-hero__toolbar,
.rotation-hero__summary,
.rotation-hero__title,
.rotation-hero__actions {
  display: flex;
  gap: 16px;
}

.rotation-hero__main,
.rotation-hero__toolbar {
  justify-content: space-between;
  align-items: flex-start;
}

.rotation-hero__title {
  align-items: center;
  margin-top: 4px;
}

.rotation-hero__title h1 {
  margin: 0;
}

.rotation-hero__toolbar {
  flex-wrap: wrap;
}

.rotation-hero__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.rotation-table-card {
  margin-top: 24px;
}

@media (max-width: 1080px) {
  .rotation-hero__main,
  .rotation-hero__toolbar {
    flex-direction: column;
  }

  .rotation-hero__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .rotation-hero__title,
  .rotation-hero__actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .rotation-hero__summary {
    grid-template-columns: 1fr;
  }
}
</style>
