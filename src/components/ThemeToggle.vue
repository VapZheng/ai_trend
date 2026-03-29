<script setup lang="ts">
import { useDarkMode } from '../composables/useDarkMode';

const { isDarkMode, toggleDarkMode } = useDarkMode();
</script>

<template>
  <el-button
    :icon="isDarkMode ? 'Sunny' : 'Moon'"
    circle
    @click="toggleDarkMode"
    :title="isDarkMode ? '切换到浅色模式' : '切换到深色模式'"
    aria-label="切换深色模式"
  />
</template>

<style scoped>
:deep(.el-button) {
  transition: all 200ms ease-out;
}

:deep(.el-button:hover) {
  transform: scale(1.1);
}
</style>
