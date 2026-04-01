<template>
  <div class="dynasty-chart">
    <div class="chart-header">
      <h3>朝代分布</h3>
      <span class="chart-subtitle">学习诗词的朝代统计</span>
    </div>
    <v-chart :option="chartOption" autoresize class="chart-container" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import type { EChartsOption } from 'echarts'

use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
])

interface Props {
  data: Array<{ dynasty: string; count: number }>
}

const props = defineProps<Props>()

const chartOption = computed<EChartsOption>(() => {
  
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 首 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      textStyle: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '朝代',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          fontSize: 12
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          }
        },
        data: props.data.map(item => ({
          name: item.dynasty,
          value: item.count
        }))
      }
    ]
  }
})
</script>

<style scoped>
.dynasty-chart {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 16px;
}

.chart-header h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: bold;
  color: #2C3E50;
  font-family: 'STKaiti', 'KaiTi', serif;
}

.chart-subtitle {
  font-size: 12px;
  color: #7F8C8D;
}

.chart-container {
  flex: 1;
  min-height: 280px;
}
</style>
