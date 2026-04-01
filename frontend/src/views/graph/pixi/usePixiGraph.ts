import {
  computed,
  nextTick,
  onMounted,
  onUnmounted,
  ref,
  shallowRef,
  watch,
  type Ref,
  type ShallowRef,
} from 'vue'
import type {
  DynastyItem,
  DynastyProfile,
  GraphData,
  PoetProfile,
  PoetRelation,
} from '@/api/graph'
import { GraphStage } from './GraphStage'
import { buildGraphScene } from './layout'
import type { GraphRenderEdge, GraphRenderNode, GraphScene, GraphViewLevel } from './types'

interface UsePixiGraphOptions {
  containerRef: Ref<HTMLElement | null>
  labelLayerRef: Ref<HTMLElement | null>
  viewLevel: Ref<GraphViewLevel>
  dynastyList: Ref<DynastyItem[]>
  graphData: ShallowRef<GraphData | null>
  currentDynasty: Ref<string | null>
  currentAuthor: Ref<string | null>
  poetProfiles: ShallowRef<Record<string, PoetProfile>>
  poetRelations: ShallowRef<PoetRelation[]>
  dynastyProfiles: ShallowRef<Record<string, DynastyProfile>>
  selectedNodeId: Ref<string | null>
  onNodeClick: (node: GraphRenderNode) => void
  onEdgeClick: (edge: GraphRenderEdge) => void
}

export function usePixiGraph(options: UsePixiGraphOptions) {
  const stage = shallowRef<GraphStage | null>(null)
  const resizeObserver = shallowRef<ResizeObserver | null>(null)
  const size = ref({ width: 0, height: 0 })
  const hoveredNodeId = ref<string | null>(null)
  const hoveredEdgeId = ref<string | null>(null)

  const isMobile = computed(() => size.value.width < 900)
  const scene = computed<GraphScene | null>(() => {
    if (size.value.width <= 0 || size.value.height <= 0) return null

    return buildGraphScene({
      viewLevel: options.viewLevel.value,
      dynastyList: options.dynastyList.value,
      graphData: options.graphData.value,
      currentDynasty: options.currentDynasty.value,
      currentAuthor: options.currentAuthor.value,
      poetProfiles: options.poetProfiles.value,
      poetRelations: options.poetRelations.value,
      dynastyProfiles: options.dynastyProfiles.value,
      size: size.value,
      isMobile: isMobile.value,
    })
  })

  const ensureStage = async () => {
    if (stage.value || !options.containerRef.value || !options.labelLayerRef.value) return

    const graphStage = new GraphStage({
      host: options.containerRef.value,
      labelHost: options.labelLayerRef.value,
      onNodeClick: options.onNodeClick,
      onEdgeClick: options.onEdgeClick,
      onHoverChange: ({ hoveredNodeId: nextNodeId, hoveredEdgeId: nextEdgeId }) => {
        hoveredNodeId.value = nextNodeId
        hoveredEdgeId.value = nextEdgeId
      },
    })

    await graphStage.init()
    graphStage.setSelectedNode(options.selectedNodeId.value)
    stage.value = graphStage

    if (scene.value) {
      graphStage.setScene(scene.value)
    }
  }

  const syncSize = () => {
    const element = options.containerRef.value
    if (!element) return

    size.value = {
      width: Math.max(Math.round(element.clientWidth), 1),
      height: Math.max(Math.round(element.clientHeight), 1),
    }

    stage.value?.resize(size.value.width, size.value.height)
  }

  onMounted(async () => {
    await nextTick()
    syncSize()
    await ensureStage()

    if (options.containerRef.value) {
      resizeObserver.value = new ResizeObserver(() => {
        syncSize()
      })
      resizeObserver.value.observe(options.containerRef.value)
    }
  })

  onUnmounted(() => {
    resizeObserver.value?.disconnect()
    resizeObserver.value = null
    stage.value?.destroy()
    stage.value = null
  })

  watch(scene, (nextScene) => {
    stage.value?.setScene(nextScene)
  })

  watch(
    options.selectedNodeId,
    (nextSelectedNodeId) => {
      stage.value?.setSelectedNode(nextSelectedNodeId)
      if (nextSelectedNodeId) {
        stage.value?.focusNode(nextSelectedNodeId)
      }
    },
    { immediate: true },
  )

  return {
    scene,
    hoveredNodeId,
    hoveredEdgeId,
    zoomIn: () => stage.value?.zoomIn(),
    zoomOut: () => stage.value?.zoomOut(),
    resetView: () => stage.value?.resetView(),
    focusNode: (nodeId: string | null) => stage.value?.focusNode(nodeId),
  }
}
