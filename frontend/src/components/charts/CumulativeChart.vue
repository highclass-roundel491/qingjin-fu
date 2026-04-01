<template>
  <div class="cumulative-chart">
    <div class="chart-header">
      <h3>累计学习诗词</h3>
      <span class="chart-subtitle">学习诗词数量增长趋势</span>
    </div>
    <v-chart :option="chartOption" autoresize class="chart-container" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent
} from 'echarts/components'
import type { EChartsOption } from 'echarts'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent
])

interface Props {
  data: Array<{ date: string; total: number }>
}

const props = defineProps<Props>()

const chartOption = computed<EChartsOption>(() => {
  const dates = props.data.map(item => item.date.slice(5))
  const totals = props.data.map(item => item.total)

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const param = params[0]
        return `${param.name}<br/>累计: ${param.value} 首`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLabel: {
        fontSize: 12
      }
    },
    yAxis: {
      type: 'value',
      name: '首',
      minInterval: 1,
      axisLabel: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '累计诗词',
        type: 'line',
        smooth: true,
        data: totals,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(22, 160, 133, 0.4)' },
              { offset: 1, color: 'rgba(22, 160, 133, 0.05)' }
            ]
          }
        },
        lineStyle: {
          width: 3,
          color: '#16A085'
        },
        itemStyle: {
          color: '#16A085'
        }
      }
    ]
  }
})
</script>

<style scoped>
.cumulative-chart {
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
  min-height: 250px;
}
</style>
