<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const sourceLabel = { window: '窗内', request: '覆盖值', default: '默认' }
const parse = (t) => { try { return JSON.parse(t) } catch { return {} } }
const dash = (v) => (v === null || v === undefined || v === '' ? '—' : v)
onMounted(async () => {
  const rows = (await getJSON('/api/history')).items
  items.value = rows.map(h => {
    const input = h.input || parse(h.input_json)
    const result = h.result || parse(h.result_json)
    return { ...h, input, result }
  })
})
</script>
<template><div class="page"><h1>估算记录</h1><table>
<tr><th>#</th><th>时间</th><th>房间</th><th>施工日</th><th>所用涂布率</th><th>来源</th><th>升数</th></tr>
<tr v-for="h in items" :key="h.id">
  <td>#{{ h.id }}</td>
  <td>{{ h.created_at }}</td>
  <td>{{ dash(h.input.room_id) }}</td>
  <td>{{ dash(h.input.work_date) }}</td>
  <td>{{ dash(h.result.coverage ?? h.input.coverage) }}</td>
  <td>{{ sourceLabel[h.result.coverage_source ?? h.input.coverage_source] ?? '—' }}</td>
  <td>{{ dash(h.result.liters) }}</td>
</tr>
</table>
<p class="muted">所用涂布率与升数为写入时钉选口径，不再随后续季节窗配置变动。</p>
</div></template>
