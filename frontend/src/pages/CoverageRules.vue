<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const s = ref({})
const win = ref({ enabled: false, start_md: '', end_md: '', coverage: '' })
const msg = ref('')
const err = ref('')
onMounted(async () => {
  s.value = await getJSON('/api/settings')
  const w = await getJSON('/api/settings/season-window')
  win.value = {
    enabled: w.enabled,
    start_md: w.start_md ?? '',
    end_md: w.end_md ?? '',
    coverage: w.coverage ?? '',
  }
})
const save = async () => {
  msg.value = ''; err.value = ''
  try {
    const saved = await postJSON('/api/settings/season-window', {
      enabled: win.value.enabled,
      start_md: win.value.start_md,
      end_md: win.value.end_md,
      coverage: Number(win.value.coverage),
    })
    win.value = { enabled: saved.enabled, start_md: saved.start_md, end_md: saved.end_md, coverage: String(saved.coverage) }
    msg.value = '窗口已保存'
  } catch (e) {
    err.value = '保存被拒绝：' + e.message
  }
}
</script>
<template><div class="page"><h1>遮盖力参数</h1>
<p>每升可刷 {{ s.coverage }} m² · 默认 {{ s.coats }} 遍（窗外且未给覆盖值时使用）</p>
<h2>季节窗口</h2>
<label><input type="checkbox" v-model="win.enabled" /> 启用窗口</label>
<p v-if="!win.enabled" class="muted">窗口已停用：新测一律走请求体覆盖值或系统默认涂布率。</p>
<div class="form-row">
  <label>起（月-日）<input v-model="win.start_md" placeholder="06-01" /></label>
  <label>止（月-日）<input v-model="win.end_md" placeholder="08-31" /></label>
  <label>窗内涂布率（m²/升）<input v-model="win.coverage" placeholder="6" /></label>
</div>
<button @click="save">保存窗口</button>
<p v-if="msg" class="ok">{{ msg }}</p>
<p v-if="err" class="err">{{ err }}</p>
<p class="muted">说明：施工日落入窗内（含起止当日，不支持跨年）时用窗内涂布率；窗内率须为正，起月日不得晚于止月日。</p>
</div></template>
