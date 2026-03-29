<script setup lang="ts">
import { ref } from 'vue';
import type { SectorRotationTarget } from '../types';

defineProps<{
  isSaving: boolean;
  modelValue: boolean;
  targets: SectorRotationTarget[];
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  add: [code: string];
  remove: [code: string];
}>();

const pendingCode = ref('');

function handleAdd() {
  const code = pendingCode.value.trim().toUpperCase();
  if (code.length === 0) {
    return;
  }
  emit('add', code);
  pendingCode.value = '';
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    destroy-on-close
    title="代码配置"
    width="780px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="rotation-config">
      <div class="rotation-config__form">
        <el-input
          v-model="pendingCode"
          clearable
          placeholder="输入板块或指数代码，如 BK0428 / 000300"
          size="large"
          @keyup.enter="handleAdd"
        />
        <el-button :loading="isSaving" size="large" type="primary" @click="handleAdd">添加代码</el-button>
      </div>

      <p class="rotation-config__hint">
        系统会实时向东财解析真实名称与行情标识，并将配置写入 sqlite；增删代码后会立即刷新榜单。
      </p>

      <el-table v-if="targets.length > 0" :data="targets" size="small">
        <el-table-column prop="code" label="代码" min-width="120" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="securityTypeName" label="类型" min-width="100" />
        <el-table-column prop="quoteId" label="行情标识" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作" min-width="100" align="center">
          <template #default="scope">
            <el-button :loading="isSaving" link type="danger" @click="emit('remove', scope.row.code)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="当前还没有配置代码，先添加需要跟踪的板块或指数。" />
    </div>
  </el-dialog>
</template>

<style scoped>
.rotation-config {
  display: grid;
  gap: 16px;
}

.rotation-config__form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.rotation-config__hint {
  margin: 0;
  color: #64748b;
}

@media (max-width: 768px) {
  .rotation-config__form {
    grid-template-columns: 1fr;
  }
}
</style>
