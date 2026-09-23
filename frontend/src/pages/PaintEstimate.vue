<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const room_id = ref(1)
const work_date = ref('')
const coverage = ref('')
const out = ref(null)
const sourceLabel = { window: '窗内涂布率', request: '请求覆盖值', default: '系统默认涂布率' }
const run = async () => {
  const body = { room_id: room_id.value, persist: true }
  if (work_date.value) body.work_date = work_date.value
  if (coverage.value !== '') body.coverage = Number(coverage.value)
  out.value = await postJSON('/api/estimate', body)
}
</script>
<template><div class="page"><h1>估漆工作台</h1>
<label>房间ID <input v-model.number="room_id" /></label>
<label>施工日 <input type="date" v-model="work_date" /></label>
<label>覆盖涂布率（可选，窗外才生效）<input v-model="coverage" placeholder="留空走系统默认" /></label>
<button @click="run">估算</button>
<template v-if="out">
  <p>净 {{ out.net_m2 }} m² · {{ out.liters }} 升 · {{ out.coats }} 遍</p>
  <p>判定所用涂布率：<strong>{{ out.coverage }} m²/升</strong>（{{ sourceLabel[out.coverage_source] ?? out.coverage_source }}）<template v-if="out.work_date"> · 施工日 {{ out.work_date }}</template></p>
</template>
</div></template>
