<template>
  <div class="study-time-chart">
    <div class="chart-header">
      <h3>学习时长趋势</h3>
      <span class="chart-subtitle">近期学习时长统计</span>
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
  GridComponent,
  LegendComponent
} from 'echarts/components'
import type { EChartsOption } from 'echarts'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
])

interface Props {
  data: Array<{ date: string; duration: number }>
}

const props = defineProps<Props>()

const chartOption = computed<EChartsOption>(() => {
  const dates = props.data.map(item => item.date.slice(5))
  const durations = props.data.map(item => Math.round(item.duration / 60))

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const param = params[0]
        return `${param.name}<br/>学习时长: ${param.value} 分钟`
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
      name: '分钟',
      minInterval: 1,
      axisLabel: {
        fontSize: 12
      }
    },
    series: [
      {
        name: '学习时长',
        type: 'line',
        smooth: true,
        data: durations,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(44, 62, 80, 0.3)' },
              { offset: 1, color: 'rgba(44, 62, 80, 0.05)' }
            ]
          }
        },
        lineStyle: {
          width: 3,
          color: '#2C3E50'
        },
        itemStyle: {
          color: '#2C3E50'
        }
      }
    ]
  }
})
</script>

<style scoped>
.study-time-chart {
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
