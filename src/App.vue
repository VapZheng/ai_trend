<script setup lang="ts">
import { computed, ref } from 'vue';
import DashboardPage from './components/DashboardPage.vue';
import SectorRotationPage from './components/SectorRotationPage.vue';
import ThemeToggle from './components/ThemeToggle.vue';
import type { AppPageKey } from './types';

const activePage = ref<AppPageKey>('dashboard');
const mountedPages = ref<AppPageKey[]>(['dashboard']);
const pageTabs: Array<{ description: string; label: string; value: AppPageKey }> = [
  {
    description: '保留原主流程，查看市场趋势、筛选、对比与图表。',
    label: '趋势看板',
    value: 'dashboard',
  },
  {
    description: '独立查看板块轮动榜单、代码配置与历史明细。',
    label: '板块轮动',
    value: 'sector-rotation',
  },
];

const activePageMeta = computed(() => {
  return pageTabs.find((item) => item.value === activePage.value) ?? pageTabs[0];
});


function isPageMounted(page: AppPageKey): boolean {
  return mountedPages.value.includes(page);
}

function handlePageChange(page: AppPageKey) {
  if (!mountedPages.value.includes(page)) {
    mountedPages.value = [...mountedPages.value, page];
  }
  activePage.value = page;
}
</script>

<template>
  <div class="page-shell">
    <main class="page-main app-main">
      <section class="app-switcher">
        <div>
          <p class="eyebrow">AI Trend Dashboard</p>
          <h2>市场趋势与板块轮动</h2>
          <p class="app-switcher__note">{{ activePageMeta.description }}</p>
        </div>

        <div class="app-switcher__controls">
          <div class="app-switcher__tabs" role="tablist" aria-label="页面切换">
            <button
              v-for="item in pageTabs"
              :key="item.value"
              :aria-selected="activePage === item.value"
              :class="['app-page-tab', { 'app-page-tab--active': activePage === item.value }]"
              role="tab"
              type="button"
              @click="handlePageChange(item.value)"
            >
              {{ item.label }}
            </button>
          </div>

          <ThemeToggle />
        </div>
      </section>

      <section v-show="activePage === 'dashboard'" class="app-page-stage" role="tabpanel">
        <DashboardPage />
      </section>

      <section v-show="activePage === 'sector-rotation'" class="app-page-stage" role="tabpanel">
        <SectorRotationPage v-if="isPageMounted('sector-rotation')" />
      </section>
    </main>
  </div>
</template>

<style scoped>
.app-main {
  display: grid;
  gap: 24px;
}

.app-page-stage {
  min-width: 0;
}

.app-switcher {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 18px 22px;
  border: 1px solid var(--color-border);
  border-radius: 24px;
  background: var(--color-card-bg);
  box-shadow: var(--shadow-md);
  transition: all 200ms ease-out;
}

.app-switcher h2,
.app-switcher__note {
  margin: 0;
}

.app-switcher h2 {
  color: var(--color-text-primary);
}

.app-switcher__note {
  margin-top: 8px;
  color: var(--color-text-tertiary);
}

.app-switcher__controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.app-switcher__tabs {
  display: inline-flex;
  gap: 10px;
  padding: 6px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-bg-secondary);
  transition: all 200ms ease-out;
}

.app-page-tab {
  min-height: 44px;
  padding: 0 18px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-weight: 600;
  transition:
    background-color 200ms ease,
    color 200ms ease,
    box-shadow 200ms ease;
}

.app-page-tab:hover {
  background: var(--color-bg-tertiary);
}

.app-page-tab:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.app-page-tab--active {
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.24);
}

@media (max-width: 768px) {
  .app-switcher {
    flex-direction: column;
    align-items: flex-start;
  }

  .app-switcher__controls {
    width: 100%;
    justify-content: space-between;
  }

  .app-switcher__tabs {
    flex: 1;
    justify-content: stretch;
  }

  .app-page-tab {
    flex: 1;
  }
}
</style>
