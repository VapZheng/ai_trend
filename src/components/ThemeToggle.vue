<script setup lang="ts">
import { useDarkMode } from '../composables/useDarkMode';

const { isDarkMode, toggleDarkMode } = useDarkMode();
</script>

<template>
  <div class="theme-toggle">
    <el-button
      :icon="isDarkMode ? 'Sunny' : 'Moon'"
      circle
      @click="toggleDarkMode"
      :title="isDarkMode ? '切换到浅色模式' : '切换到深色模式'"
      aria-label="切换深色模式"
      class="theme-toggle__button"
    />
  </div>
</template>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
}

.theme-toggle__button {
  transition: all 200ms ease-out;
}

.theme-toggle__button:hover {
  transform: scale(1.1) rotate(20deg);
}

.theme-toggle__button:active {
  transform: scale(0.95);
}

:deep(.el-button) {
  border-color: var(--color-border);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

:deep(.el-button:hover) {
  background: var(--color-bg-tertiary);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

:deep(.el-button:focus) {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
</style>

