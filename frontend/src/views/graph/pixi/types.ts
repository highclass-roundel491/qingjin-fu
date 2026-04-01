import type {
  DynastyItem,
  DynastyProfile,
  GraphData,
  GraphLink,
  GraphNode,
  PoetProfile,
  PoetRelation,
} from '@/api/graph'

export type GraphViewLevel = 0 | 1 | 2

export type GraphNodeType = 'dynasty' | 'poet' | 'category'
export type GraphNodeTier = 'core' | 'major' | 'minor'
export type GraphEdgeKind = 'semantic' | 'structural' | 'ambient'

export interface GraphSceneSize {
  width: number
  height: number
}

export interface GraphSceneInput {
  viewLevel: GraphViewLevel
  dynastyList: DynastyItem[]
  graphData: GraphData | null
  currentDynasty: string | null
  currentAuthor: string | null
  poetProfiles: Record<string, PoetProfile>
  poetRelations: PoetRelation[]
  dynastyProfiles: Record<string, DynastyProfile>
  size: GraphSceneSize
  isMobile: boolean
}

export interface NodeTone {
  core: string
  halo: string
  label: string
  accent: string
}

export interface GraphRenderNode {
  id: string
  name: string
  type: GraphNodeType
  tier: GraphNodeTier
  importance: number
  x: number
  y: number
  targetX: number
  targetY: number
  radius: number
  color: string
  glow: number
  labelVisible: boolean
  dynasty?: string
  subtitle?: string
  description?: string
  labelPriority: number
  depth: number
  rawData?: GraphNode | DynastyItem
}

export interface GraphRenderEdge {
  id: string
  sourceId: string
  targetId: string
  weight: number
  kind: GraphEdgeKind
  label?: string
  glowStrength: number
  alpha: number
  curve: number
  isSemantic: boolean
  emphasis: number
  flow: boolean
  rawData?: GraphLink
}

export interface GraphSceneBounds {
  minX: number
  minY: number
  maxX: number
  maxY: number
  width: number
  height: number
}

export interface GraphScene {
  key: string
  level: GraphViewLevel
  nodes: GraphRenderNode[]
  edges: GraphRenderEdge[]
  centerNodeId?: string
  bounds: GraphSceneBounds
  worldPadding: number
  maxLabels: number
  particleDensity: number
  isMobile: boolean
}

export interface GraphInteractionState {
  hoveredNodeId: string | null
  hoveredEdgeId: string | null
  selectedNodeId: string | null
}

export interface EdgeAnchor {
  id: string
  label?: string
  x: number
  y: number
}

export interface LabelOverlayState extends GraphInteractionState {
  edgeAnchors: EdgeAnchor[]
}

export const GRAPH_WORLD_PADDING = 180

export const GRAPH_BACKGROUND = {
  base: '#05070b',
  edgeSemantic: '#eadfbe',
  edgeStructural: '#96a7c8',
  edgeAmbient: '#d8e3f5',
}

const POET_TONES: Array<{ threshold: number; tone: NodeTone }> = [
  {
    threshold: 82,
    tone: {
      core: '#f6e2a9',
      halo: '#f0c96f',
      label: '#fff5de',
      accent: '#f3d796',
    },
  },
  {
    threshold: 64,
    tone: {
      core: '#f4b58c',
      halo: '#de8669',
      label: '#fff1e6',
      accent: '#ebb38d',
    },
  },
  {
    threshold: 46,
    tone: {
      core: '#b7d7ea',
      halo: '#74a9cf',
      label: '#eef7ff',
      accent: '#a6cade',
    },
  },
  {
    threshold: 24,
    tone: {
      core: '#9fc9c3',
      halo: '#6faaa3',
      label: '#eafaf6',
      accent: '#8dc3bc',
    },
  },
  {
    threshold: 0,
    tone: {
      core: '#a7b6d9',
      halo: '#6f81b7',
      label: '#e8effd',
      accent: '#97a6cf',
    },
  },
]

export function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

export function normalizeValue(
  value: number,
  min: number,
  max: number,
  fallback = 0.5,
) {
  if (!Number.isFinite(value)) return fallback
  if (max <= min) return fallback
  return clamp((value - min) / (max - min), 0, 1)
}

export function getNodeType(category: number): GraphNodeType {
  if (category === 0) return 'dynasty'
  if (category === 1) return 'poet'
  return 'category'
}

export function getPoetTone(influence?: number): NodeTone {
  const score = influence ?? 48
  for (const item of POET_TONES) {
    if (score >= item.threshold) return item.tone
  }
  return POET_TONES[POET_TONES.length - 1]!.tone
}
