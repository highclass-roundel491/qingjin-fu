import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceRadial,
  forceSimulation,
  forceX,
  forceY,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from 'd3-force'
import type { GraphNode, PoetRelation } from '@/api/graph'
import {
  GRAPH_WORLD_PADDING,
  getPoetTone,
  normalizeValue,
  type GraphEdgeKind,
  type GraphRenderEdge,
  type GraphRenderNode,
  type GraphScene,
  type GraphSceneInput,
  type GraphSceneSize,
  type GraphViewLevel,
} from './types'

interface LayoutHint {
  baseRadius: number
  zoneAngle: number
  zoneSpread: number
  anchorX: number
  anchorY: number
}

interface LayoutNode extends SimulationNodeDatum {
  id: string
  ref: GraphRenderNode
  baseRadius: number
  anchorX: number
  anchorY: number
}

interface LayoutLink extends SimulationLinkDatum<LayoutNode> {
  source: string
  target: string
  distance: number
  strength: number
}

export function buildGraphScene(input: GraphSceneInput): GraphScene | null {
  if (input.viewLevel === 0) {
    return buildDynastyScene(input)
  }
  if (input.viewLevel === 1) {
    return buildDynastyFocusScene(input)
  }
  return buildAuthorScene(input)
}

function buildDynastyScene(input: GraphSceneInput): GraphScene | null {
  if (!input.dynastyList.length) return null

  const counts = input.dynastyList.map((item) => item.count)
  const maxCount = Math.max(...counts)
  const minCount = Math.min(...counts)
  const nodes = input.dynastyList.map((item, index) => {
    const importance = normalizeValue(item.count, minCount, maxCount, 0.52)
    const tier = index < (input.isMobile ? 4 : 6) ? 'major' : 'minor'
    const radius = Math.round(22 + importance * 40)
    const profile = input.dynastyProfiles[item.name]

    return {
      id: `dynasty_${item.name}`,
      name: item.name,
      type: 'dynasty',
      tier,
      importance,
      x: 0,
      y: 0,
      targetX: 0,
      targetY: 0,
      radius,
      color: tier === 'major' ? '#f0cb79' : '#d1ae65',
      glow: 0.58 + importance * 0.38,
      labelVisible: index < (input.isMobile ? 2 : 3),
      subtitle: compactDynastyCopy(profile?.poem_count_label) ?? `${item.count} 首`,
      description: profile?.description,
      labelPriority: 110 - index * 6,
      depth: 0.56 + importance * 0.2,
      rawData: item,
    } satisfies GraphRenderNode
  })

  const guideEdges = buildGuideEdges(nodes, 1, 'ambient')
  const hints = new Map<string, LayoutHint>()
  const random = createSeededRandom(hashText('dynasty-scene'))
  const anchorAngles = [-0.18, Math.PI * 0.86, Math.PI * 1.42, Math.PI * 0.22]

  nodes.forEach((node, index) => {
    const importanceBias = 1 - node.importance * 0.45
    const band = 220 + index * 110 * importanceBias
    const angle = (anchorAngles[index] ?? (-Math.PI * 0.25 + random() * Math.PI * 1.5)) + (random() - 0.5) * 0.12
    hints.set(node.id, {
      baseRadius: band,
      zoneAngle: angle,
      zoneSpread: 0.32,
      anchorX: Math.cos(angle) * band * 0.18,
      anchorY: Math.sin(angle) * band * 0.12,
    })
  })

  runForceLayout({
    key: 'dynasty-scene',
    nodes,
    edges: guideEdges,
    hints,
    iterations: 280,
  })

  const ambientEdges = buildAmbientEdges(nodes, guideEdges, input.isMobile ? 2 : 4, 460)

  return finalizeScene({
    key: 'level0:dynasties',
    level: 0,
    size: input.size,
    nodes,
    edges: dedupeEdges([...guideEdges, ...ambientEdges]),
    isMobile: input.isMobile,
  })
}

function buildDynastyFocusScene(input: GraphSceneInput): GraphScene | null {
  if (!input.graphData || !input.currentDynasty) return null

  const poets = input.graphData.nodes.filter((node) => node.category === 1)
  if (!poets.length) return null

  const values = poets.map((node) => getNodeImportance(node, input.poetProfiles))
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)

  const centerNode: GraphRenderNode = {
    id: `dynasty_${input.currentDynasty}`,
    name: input.currentDynasty,
    type: 'dynasty',
    tier: 'core',
    importance: 1,
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
    radius: input.isMobile ? 38 : 48,
    color: '#f3d27a',
    glow: 1.05,
    labelVisible: true,
    subtitle:
      compactDynastyCopy(input.dynastyProfiles[input.currentDynasty]?.poem_count_label)
      ?? input.dynastyProfiles[input.currentDynasty]?.influence,
    description: input.dynastyProfiles[input.currentDynasty]?.description,
    labelPriority: 200,
    depth: 1,
    rawData: {
      id: `dynasty_${input.currentDynasty}`,
      name: input.currentDynasty,
      category: 0,
      value: poets.length,
      symbolSize: 80,
      poem_count: poets.length,
    } satisfies GraphNode,
  }

  const poetNodes = poets
    .slice()
    .sort((left, right) => getNodeImportance(right, input.poetProfiles) - getNodeImportance(left, input.poetProfiles))
    .map((node, index) => {
      const tone = getPoetTone(resolveInfluence(node, input.poetProfiles))
      const importance = normalizeValue(getNodeImportance(node, input.poetProfiles), minValue, maxValue, 0.48)
      const tier = index < (input.isMobile ? 3 : 5) || importance >= 0.84 ? 'major' : 'minor'
      const radius = tier === 'major'
        ? Math.round(16 + importance * 18)
        : Math.round(8 + importance * 10)

      return {
        id: node.id,
        name: node.name,
        type: 'poet',
        tier,
        importance,
        x: 0,
        y: 0,
        targetX: 0,
        targetY: 0,
        radius,
        color: tone.core,
        glow: tier === 'major' ? 0.74 + importance * 0.22 : 0.3 + importance * 0.12,
        labelVisible: tier === 'major' && index < (input.isMobile ? 3 : 5),
        dynasty: node.dynasty,
        subtitle: input.poetProfiles[node.name]?.alias,
        description: input.poetProfiles[node.name]?.description ?? node.representative_work,
        labelPriority: tier === 'major' ? 120 - index * 4 : 52 - index,
        depth: tier === 'major' ? 0.82 : 0.38 + importance * 0.12,
        rawData: node,
      } satisfies GraphRenderNode
    })

  const nodes = [centerNode, ...poetNodes]
  const edges: GraphRenderEdge[] = poetNodes.map((node, index) => ({
    id: `dynasty-link:${centerNode.id}:${node.id}`,
    sourceId: centerNode.id,
    targetId: node.id,
    weight: 1 + node.importance,
    kind: 'structural',
    glowStrength: node.tier === 'major' ? 0.32 : 0.12,
    alpha: node.tier === 'major' ? 0.06 : 0.025,
    curve: createSignedCurve(index, 0.12, 0.18),
    isSemantic: false,
    emphasis: node.tier === 'major' ? 0.7 : 0.26,
    flow: node.tier === 'major',
  }))

  const hints = new Map<string, LayoutHint>()
  hints.set(centerNode.id, {
    baseRadius: 0,
    zoneAngle: 0,
    zoneSpread: 0,
    anchorX: 0,
    anchorY: 0,
  })

  const random = createSeededRandom(hashText(`dynasty:${input.currentDynasty}`))
  poetNodes.forEach((node, index) => {
    const isMajor = node.tier === 'major'
    const baseRadius = isMajor
      ? 168 + index * 22 + random() * 56
      : 318 + (index % 7) * 26 + random() * 100
    const baseAngle = isMajor
      ? -Math.PI * 0.35 + random() * Math.PI * 1.55
      : -Math.PI * 0.55 + random() * Math.PI * 1.9
    hints.set(node.id, {
      baseRadius,
      zoneAngle: baseAngle,
      zoneSpread: isMajor ? Math.PI * 0.88 : Math.PI * 1.2,
      anchorX: Math.cos(baseAngle) * baseRadius * (isMajor ? 0.18 : 0.24),
      anchorY: Math.sin(baseAngle) * baseRadius * (isMajor ? 0.22 : 0.28),
    })
  })

  runForceLayout({
    key: `dynasty:${input.currentDynasty}`,
    nodes,
    edges,
    hints,
    centerNodeId: centerNode.id,
    iterations: 320,
  })

  const ambientEdges = buildAmbientEdges(nodes, edges, input.isMobile ? 4 : 8, 320)

  return finalizeScene({
    key: `level1:${input.currentDynasty}`,
    level: 1,
    size: input.size,
    nodes,
    edges: dedupeEdges([...edges, ...ambientEdges]),
    centerNodeId: centerNode.id,
    isMobile: input.isMobile,
  })
}

function buildAuthorScene(input: GraphSceneInput): GraphScene | null {
  if (!input.graphData || !input.currentAuthor) return null

  const authorId = `author_${input.currentAuthor}`
  const centerRaw = input.graphData.nodes.find((node) => node.id === authorId)
  if (!centerRaw) return null

  const centerTone = getPoetTone(resolveInfluence(centerRaw, input.poetProfiles))
  const centerNode: GraphRenderNode = {
    id: centerRaw.id,
    name: centerRaw.name,
    type: 'poet',
    tier: 'core',
    importance: 1,
    x: 0,
    y: 0,
    targetX: 0,
    targetY: 0,
    radius: input.isMobile ? 40 : 50,
    color: centerTone.core,
    glow: 1.18,
    labelVisible: true,
    dynasty: centerRaw.dynasty,
    subtitle: input.poetProfiles[centerRaw.name]?.alias,
    description: input.poetProfiles[centerRaw.name]?.description ?? centerRaw.representative_work,
    labelPriority: 220,
    depth: 1,
    rawData: centerRaw,
  }

  const linkedIds = new Set<string>()
  const rawEdges = input.graphData.links.filter((edge) => edge.source === authorId || edge.target === authorId)
  rawEdges.forEach((edge) => {
    linkedIds.add(edge.source === authorId ? edge.target : edge.source)
  })

  const curatedRelations = getCuratedRelations(input.currentAuthor, input.poetRelations)
  curatedRelations.forEach((relation) => linkedIds.add(`author_${relation.other}`))

  const linkedNodes = input.graphData.nodes.filter((node) => linkedIds.has(node.id))
  const poetSatellites = linkedNodes
    .filter((node) => node.category === 1)
    .sort((left, right) => getNodeImportance(right, input.poetProfiles) - getNodeImportance(left, input.poetProfiles))
    .slice(0, input.isMobile ? 24 : 40)
  const structuralNodes = linkedNodes
    .filter((node) => node.category !== 1)
    .sort((left, right) => getNodeImportance(right, input.poetProfiles) - getNodeImportance(left, input.poetProfiles))
    .slice(0, input.isMobile ? 3 : 5)

  const poetValues = poetSatellites.length
    ? poetSatellites.map((node) => getNodeImportance(node, input.poetProfiles))
    : [1]
  const minValue = Math.min(...poetValues)
  const maxValue = Math.max(...poetValues)

  const poetNodes = poetSatellites
    .slice()
    .map((node, index) => {
      const tone = getPoetTone(resolveInfluence(node, input.poetProfiles))
      const importance = normalizeValue(getNodeImportance(node, input.poetProfiles), minValue, maxValue, 0.54)
      const tier = index < (input.isMobile ? 5 : 8) || importance >= 0.74 ? 'major' : 'minor'
      const radius = tier === 'major'
        ? Math.round(18 + importance * 18)
        : Math.round(6 + importance * 7)

      return {
        id: node.id,
        name: node.name,
        type: 'poet',
        tier,
        importance,
        x: 0,
        y: 0,
        targetX: 0,
        targetY: 0,
        radius,
        color: tone.core,
        glow: tier === 'major' ? 0.82 + importance * 0.24 : 0.3 + importance * 0.14,
        labelVisible: tier === 'major'
          ? index < (input.isMobile ? 5 : 9)
          : index < (input.isMobile ? 8 : 14) && importance >= 0.46,
        dynasty: node.dynasty,
        subtitle: input.poetProfiles[node.name]?.alias,
        description: input.poetProfiles[node.name]?.description ?? node.representative_work,
        labelPriority: tier === 'major' ? 156 - index * 4 : 74 - index,
        depth: tier === 'major' ? 0.9 : 0.4 + importance * 0.16,
        rawData: node,
      } satisfies GraphRenderNode
    })

  const supportNodes = structuralNodes.map((node, index) => {
    const isDynasty = node.category === 0
    const radius = isDynasty ? 16 : 5 + (index % 2) * 1.5

    return {
      id: node.id,
      name: node.name,
      type: isDynasty ? 'dynasty' : 'category',
      tier: isDynasty ? 'major' : 'minor',
      importance: isDynasty ? 0.46 : 0.18,
      x: 0,
      y: 0,
      targetX: 0,
      targetY: 0,
      radius,
      color: isDynasty ? '#d4b16e' : '#82b5ac',
      glow: isDynasty ? 0.26 : 0.1,
      labelVisible: false,
      dynasty: node.dynasty,
      subtitle: isDynasty
        ? compactDynastyCopy(input.dynastyProfiles[node.name]?.poem_count_label)
        : undefined,
      description: isDynasty
        ? input.dynastyProfiles[node.name]?.description
        : `题材星屑 · ${node.poem_count ?? node.value} 首`,
      labelPriority: isDynasty ? 46 : 12 - index,
      depth: isDynasty ? 0.46 : 0.14,
      rawData: node,
    } satisfies GraphRenderNode
  })

  const nodes = [centerNode, ...poetNodes, ...supportNodes]
  const edges: GraphRenderEdge[] = []

  rawEdges.forEach((edge, index) => {
    const otherId = edge.source === authorId ? edge.target : edge.source
    const otherNode = nodes.find((node) => node.id === otherId)
    if (!otherNode) return

    const isSemantic = otherNode.type === 'poet'
    const curatedLabel = isSemantic
      ? resolveRelationLabel(input.currentAuthor!, otherNode.name, input.poetRelations) ?? edge.label
      : undefined

    edges.push({
      id: `edge:${authorId}:${otherId}`,
      sourceId: authorId,
      targetId: otherId,
      weight: edge.value,
      kind: isSemantic ? 'semantic' : 'structural',
      label: curatedLabel,
      glowStrength: isSemantic ? 0.42 : 0.14,
      alpha: isSemantic ? 0.102 : 0.038,
      curve: createSignedCurve(index, isSemantic ? 0.03 : 0.02, isSemantic ? 0.11 : 0.06),
      isSemantic,
      emphasis: isSemantic ? 0.76 : 0.16,
      flow: isSemantic,
      rawData: edge,
    })
  })

  curatedRelations.forEach((relation, index) => {
    const targetId = `author_${relation.other}`
    if (!poetNodes.some((node) => node.id === targetId)) return
    if (edges.some((edge) => edge.targetId === targetId || edge.sourceId === targetId)) return

    edges.push({
      id: `edge:${authorId}:${targetId}`,
      sourceId: authorId,
      targetId,
      weight: 1.2,
      kind: 'semantic',
      label: relation.label,
      glowStrength: 0.44,
      alpha: 0.11,
      curve: createSignedCurve(index + rawEdges.length, 0.03, 0.12),
      isSemantic: true,
      emphasis: 0.82,
      flow: true,
    })
  })

  const hints = new Map<string, LayoutHint>()
  hints.set(centerNode.id, {
    baseRadius: 0,
    zoneAngle: 0,
    zoneSpread: 0,
    anchorX: 0,
    anchorY: 0,
  })

  const random = createSeededRandom(hashText(`author:${input.currentAuthor}`))
  const majorAnglePresets = input.isMobile
    ? [-2.48, -1.98, -1.46, -0.72, 0.14, 0.82, 1.38]
    : [-2.48, -2.06, -1.68, -1.12, -0.52, 0.08, 0.62, 1.14, 1.82]
  const minorStreams = input.isMobile
    ? [
      { angle: -2.46, spread: 0.2, radius: 290, step: 90, anchorX: -106, anchorY: -54 },
      { angle: -0.94, spread: 0.26, radius: 356, step: 102, anchorX: 62, anchorY: -118 },
      { angle: -0.14, spread: 0.22, radius: 468, step: 110, anchorX: 210, anchorY: -10 },
      { angle: 0.56, spread: 0.24, radius: 410, step: 104, anchorX: 152, anchorY: 92 },
      { angle: 1.18, spread: 0.2, radius: 320, step: 84, anchorX: 0, anchorY: 162 },
    ]
    : [
      { angle: -2.54, spread: 0.22, radius: 316, step: 108, anchorX: -148, anchorY: -74 },
      { angle: -0.94, spread: 0.28, radius: 388, step: 118, anchorX: 94, anchorY: -166 },
      { angle: -0.12, spread: 0.24, radius: 524, step: 136, anchorX: 316, anchorY: -18 },
      { angle: 0.48, spread: 0.26, radius: 468, step: 126, anchorX: 218, anchorY: 114 },
      { angle: 1.14, spread: 0.22, radius: 326, step: 96, anchorX: 6, anchorY: 226 },
    ]
  poetNodes.forEach((node, index) => {
    const isMajor = node.tier === 'major'
    if (isMajor) {
      const baseRadius = (input.isMobile ? 224 : 284) + (index % 4) * (input.isMobile ? 34 : 52) + random() * (input.isMobile ? 48 : 72)
      const baseAngle = (majorAnglePresets[index] ?? (-Math.PI * 0.92 + random() * Math.PI * 1.72)) + (random() - 0.5) * 0.18
      hints.set(node.id, {
        baseRadius,
        zoneAngle: baseAngle,
        zoneSpread: input.isMobile ? 0.24 : 0.28,
        anchorX: Math.cos(baseAngle) * baseRadius * 0.22,
        anchorY: Math.sin(baseAngle) * baseRadius * 0.16,
      })
      return
    }

    const stream = minorStreams[index % minorStreams.length]!
    const streamLane = Math.floor(index / minorStreams.length)
    const baseRadius = stream.radius + streamLane * stream.step + random() * (input.isMobile ? 46 : 72)
    const baseAngle = stream.angle + (random() - 0.5) * stream.spread
    hints.set(node.id, {
      baseRadius,
      zoneAngle: baseAngle,
      zoneSpread: stream.spread * 0.74,
      anchorX: stream.anchorX + Math.cos(baseAngle) * baseRadius * 0.1,
      anchorY: stream.anchorY + Math.sin(baseAngle) * baseRadius * 0.1,
    })
  })

  supportNodes.forEach((node, index) => {
    const isDynasty = node.type === 'dynasty'
    const baseAngle = isDynasty
      ? -Math.PI * 0.9 + random() * Math.PI * 0.22
      : Math.PI * 0.42 + (index % 4) * 0.36
    const baseRadius = isDynasty ? 900 + random() * 120 : 620 + index * 56
    hints.set(node.id, {
      baseRadius,
      zoneAngle: baseAngle,
      zoneSpread: isDynasty ? 0.1 : Math.PI * 0.12,
      anchorX: Math.cos(baseAngle) * baseRadius * (isDynasty ? 0.12 : 0.16),
      anchorY: Math.sin(baseAngle) * baseRadius * (isDynasty ? 0.07 : 0.14),
    })
  })

  runForceLayout({
    key: `author:${input.currentAuthor}`,
    nodes,
    edges,
    hints,
    centerNodeId: centerNode.id,
    iterations: 340,
  })

  spreadAuthorScene(nodes, centerNode.id, input.currentAuthor, input.isMobile)

  const ambientEdges = buildAmbientEdges(nodes, edges, input.isMobile ? 18 : 42, input.isMobile ? 1240 : 1380)
  const fieldEdges = buildFieldEdges(nodes, [...edges, ...ambientEdges], input.isMobile ? 10 : 26, input.isMobile ? 1320 : 1720)

  return finalizeScene({
    key: `level2:${input.currentDynasty ?? '_'}:${input.currentAuthor}`,
    level: 2,
    size: input.size,
    nodes,
    edges: dedupeEdges([...edges, ...ambientEdges, ...fieldEdges]),
    centerNodeId: centerNode.id,
    isMobile: input.isMobile,
  })
}

function getCuratedRelations(name: string, relations: PoetRelation[]) {
  return relations
    .filter((relation) => relation.source === name || relation.target === name)
    .map((relation) => ({
      other: relation.source === name ? relation.target : relation.source,
      label: relation.label,
    }))
}

function resolveRelationLabel(source: string, target: string, relations: PoetRelation[]) {
  return relations.find(
    (relation) =>
      (relation.source === source && relation.target === target) ||
      (relation.source === target && relation.target === source),
  )?.label
}

function getNodeImportance(node: GraphNode, profiles: Record<string, { influence: number }>) {
  if (node.category === 1) {
    return profiles[node.name]?.influence ?? node.influence ?? node.poem_count ?? node.value
  }
  return node.poem_count ?? node.value
}

function resolveInfluence(node: GraphNode, profiles: Record<string, { influence: number }>) {
  return profiles[node.name]?.influence ?? node.influence ?? 54
}

function runForceLayout(params: {
  key: string
  nodes: GraphRenderNode[]
  edges: GraphRenderEdge[]
  hints: Map<string, LayoutHint>
  centerNodeId?: string
  iterations: number
}) {
  const random = createSeededRandom(hashText(`${params.key}:layout`))
  const layoutNodes: LayoutNode[] = params.nodes.map((node) => {
    const hint = params.hints.get(node.id) ?? {
      baseRadius: 220,
      zoneAngle: random() * Math.PI * 2,
      zoneSpread: Math.PI * 2,
      anchorX: 0,
      anchorY: 0,
    }
    const angle = hint.zoneAngle + (random() - 0.5) * hint.zoneSpread
    const radius = hint.baseRadius * (0.84 + random() * 0.28)
    const x = Math.cos(angle) * radius + hint.anchorX
    const y = Math.sin(angle) * radius + hint.anchorY

    return {
      id: node.id,
      ref: node,
      x: node.id === params.centerNodeId ? 0 : x,
      y: node.id === params.centerNodeId ? 0 : y,
      fx: node.id === params.centerNodeId ? 0 : undefined,
      fy: node.id === params.centerNodeId ? 0 : undefined,
      baseRadius: hint.baseRadius,
      anchorX: hint.anchorX,
      anchorY: hint.anchorY,
    }
  })

  const nodeIds = new Set(layoutNodes.map((node) => node.id))
  const layoutLinks: LayoutLink[] = params.edges
    .filter((edge) => nodeIds.has(edge.sourceId) && nodeIds.has(edge.targetId))
    .map((edge) => ({
      source: edge.sourceId,
      target: edge.targetId,
      distance: resolveEdgeDistance(edge),
      strength: resolveEdgeStrength(edge),
    }))

  const simulation = forceSimulation(layoutNodes)
    .alpha(1)
    .alphaDecay(0.025)
    .velocityDecay(0.34)
    .force(
      'charge',
      forceManyBody<LayoutNode>().strength((node) => {
        if (node.id === params.centerNodeId) return -1800
        if (node.ref.tier === 'major') return -580 - node.ref.radius * 18 - node.ref.importance * 220
        return -260 - node.ref.radius * 12 - node.ref.importance * 140
      }),
    )
    .force(
      'collision',
      forceCollide<LayoutNode>().radius((node) => {
        if (node.id === params.centerNodeId) return node.ref.radius + 72
        return node.ref.radius + (node.ref.tier === 'major' ? 26 : 18)
      }).iterations(2),
    )
    .force(
      'radial',
      forceRadial<LayoutNode>((node) => {
        if (node.id === params.centerNodeId) return 0
        return node.baseRadius
      }, 0, 0).strength((node) => {
        if (node.id === params.centerNodeId) return 0
        return node.ref.tier === 'major' ? 0.15 : 0.08
      }),
    )
    .force('x', forceX<LayoutNode>((node) => node.anchorX).strength(0.05))
    .force('y', forceY<LayoutNode>((node) => node.anchorY).strength(0.05))
    .force('center', forceCenter(0, 0))

  if (layoutLinks.length > 0) {
    simulation.force(
      'link',
      forceLink<LayoutNode, LayoutLink>(layoutLinks)
        .id((node) => node.id)
        .distance((link) => link.distance)
        .strength((link) => link.strength),
    )
  }

  for (let index = 0; index < params.iterations; index += 1) {
    simulation.tick()
  }
  simulation.stop()

  layoutNodes.forEach((layoutNode) => {
    layoutNode.ref.x = layoutNode.x ?? 0
    layoutNode.ref.y = layoutNode.y ?? 0
    layoutNode.ref.targetX = layoutNode.ref.x
    layoutNode.ref.targetY = layoutNode.ref.y
  })
}

function resolveEdgeDistance(edge: GraphRenderEdge) {
  if (edge.kind === 'semantic') return 280
  if (edge.kind === 'structural') return 310
  return 220
}

function resolveEdgeStrength(edge: GraphRenderEdge) {
  if (edge.kind === 'semantic') return 0.14 + edge.emphasis * 0.1
  if (edge.kind === 'structural') return 0.08 + edge.emphasis * 0.05
  return 0.05
}

function buildGuideEdges(
  nodes: GraphRenderNode[],
  neighbors: number,
  kind: GraphEdgeKind,
) {
  const edges: GraphRenderEdge[] = []
  const sorted = [...nodes].sort((left, right) => right.importance - left.importance)

  sorted.forEach((node, index) => {
    for (let offset = 1; offset <= neighbors; offset += 1) {
      const target = sorted[index + offset]
      if (!target) continue
      edges.push({
        id: `ambient:${node.id}:${target.id}`,
        sourceId: node.id,
        targetId: target.id,
        weight: 0.2,
        kind,
        glowStrength: 0.18,
        alpha: 0.05,
        curve: createSignedCurve(index + offset, 0.08, 0.12),
        isSemantic: false,
        emphasis: 0.18,
        flow: false,
      })
    }
  })

  return dedupeEdges(edges)
}

function buildAmbientEdges(
  nodes: GraphRenderNode[],
  existingEdges: GraphRenderEdge[],
  limit: number,
  maxDistance: number,
): GraphRenderEdge[] {
  const edgePairs = new Set(existingEdges.map((edge) => toPairKey(edge.sourceId, edge.targetId)))
  const candidates: Array<{ source: GraphRenderNode; target: GraphRenderNode; score: number }> = []

  for (let leftIndex = 0; leftIndex < nodes.length; leftIndex += 1) {
    const left = nodes[leftIndex]!
    if (left.tier === 'core') continue

    for (let rightIndex = leftIndex + 1; rightIndex < nodes.length; rightIndex += 1) {
      const right = nodes[rightIndex]!
      if (right.tier === 'core') continue

      const pairKey = toPairKey(left.id, right.id)
      if (edgePairs.has(pairKey)) continue
      if (left.type === 'category' && right.type === 'category') continue

      const distance = Math.hypot(left.x - right.x, left.y - right.y)
      if (distance > maxDistance) continue

      const tierBoost = left.tier === 'major' || right.tier === 'major' ? 1.28 : 0.88
      const lineageBoost = left.type === 'poet' && right.type === 'poet' ? 1.08 : 0.92
      const score = tierBoost * lineageBoost * (1 / Math.max(Math.sqrt(distance), 1))
      candidates.push({ source: left, target: right, score })
    }
  }

  return candidates
    .sort((left, right) => right.score - left.score)
    .slice(0, limit)
    .map((candidate, index): GraphRenderEdge => ({
      id: `ambient:${candidate.source.id}:${candidate.target.id}:${index}`,
      sourceId: candidate.source.id,
      targetId: candidate.target.id,
      weight: 0.16,
      kind: 'ambient',
      glowStrength: 0.14,
      alpha: candidate.source.tier === 'major' || candidate.target.tier === 'major' ? 0.06 : 0.035,
      curve: createSignedCurve(index, 0.06, 0.12),
      isSemantic: false,
      emphasis: 0.12,
      flow: false,
    }))
}

function buildFieldEdges(
  nodes: GraphRenderNode[],
  existingEdges: GraphRenderEdge[],
  limit: number,
  maxDistance: number,
) {
  const edgePairs = new Set(existingEdges.map((edge) => toPairKey(edge.sourceId, edge.targetId)))
  const candidates: Array<{ source: GraphRenderNode; target: GraphRenderNode; score: number; distance: number }> = []
  const visualNodes = nodes.filter((node) => node.id && node.tier !== 'core' && node.type !== 'category')

  for (let leftIndex = 0; leftIndex < visualNodes.length; leftIndex += 1) {
    const left = visualNodes[leftIndex]!

    for (let rightIndex = leftIndex + 1; rightIndex < visualNodes.length; rightIndex += 1) {
      const right = visualNodes[rightIndex]!
      const pairKey = toPairKey(left.id, right.id)
      if (edgePairs.has(pairKey)) continue
      if (left.type === 'dynasty' && right.type === 'dynasty') continue

      const distance = Math.hypot(left.x - right.x, left.y - right.y)
      if (distance < 300 || distance > maxDistance) continue

      const majorBoost = left.tier === 'major' || right.tier === 'major' ? 1.36 : 0.92
      const poetBoost = left.type === 'poet' && right.type === 'poet' ? 1.18 : 0.98
      const distanceBoost = 0.56 + distance / maxDistance
      const score = (left.importance + right.importance) * majorBoost * poetBoost * distanceBoost
      candidates.push({ source: left, target: right, score, distance })
    }
  }

  return candidates
    .sort((left, right) => right.score - left.score)
    .slice(0, limit)
    .map((candidate, index): GraphRenderEdge => ({
      id: `field:${candidate.source.id}:${candidate.target.id}:${index}`,
      sourceId: candidate.source.id,
      targetId: candidate.target.id,
      weight: 0.12,
      kind: 'ambient',
      glowStrength: candidate.source.tier === 'major' || candidate.target.tier === 'major' ? 0.2 : 0.14,
      alpha: candidate.distance > maxDistance * 0.72 ? 0.032 : 0.04,
      curve: createSignedCurve(index + 1, 0.02, 0.08),
      isSemantic: false,
      emphasis: candidate.source.tier === 'major' || candidate.target.tier === 'major' ? 0.16 : 0.12,
      flow: false,
    }))
}

function finalizeScene(params: {
  key: string
  level: GraphViewLevel
  size: GraphSceneSize
  nodes: GraphRenderNode[]
  edges: GraphRenderEdge[]
  centerNodeId?: string
  isMobile: boolean
}) {
  const padding = GRAPH_WORLD_PADDING
  const minX = Math.min(...params.nodes.map((node) => node.x - node.radius * 4)) - padding
  const minY = Math.min(...params.nodes.map((node) => node.y - node.radius * 4)) - padding
  const maxX = Math.max(...params.nodes.map((node) => node.x + node.radius * 4)) + padding
  const maxY = Math.max(...params.nodes.map((node) => node.y + node.radius * 4)) + padding

  return {
    key: params.key,
    level: params.level,
    nodes: params.nodes,
    edges: params.edges,
    centerNodeId: params.centerNodeId,
    bounds: {
      minX,
      minY,
      maxX,
      maxY,
      width: Math.max(maxX - minX, 320),
      height: Math.max(maxY - minY, 320),
    },
    worldPadding: padding,
    maxLabels: resolveMaxLabels(params.level, params.isMobile),
    particleDensity: params.isMobile ? 0.62 : 1,
    isMobile: params.isMobile,
  } satisfies GraphScene
}

function resolveMaxLabels(level: GraphViewLevel, isMobile: boolean) {
  if (level === 2) return isMobile ? 10 : 16
  if (level === 1) return isMobile ? 4 : 5
  return isMobile ? 3 : 4
}

function spreadAuthorScene(
  nodes: GraphRenderNode[],
  centerNodeId: string,
  authorName: string,
  isMobile: boolean,
) {
  const random = createSeededRandom(hashText(`spread:${authorName}`))
  const centerX = isMobile ? -136 : -268
  const centerY = isMobile ? 18 : 54
  const majorOffsets = isMobile
    ? [
      { x: -138, y: -118 },
      { x: 10, y: -246 },
      { x: 188, y: -170 },
      { x: 262, y: 18 },
      { x: 186, y: 188 },
      { x: -10, y: 254 },
      { x: -156, y: 152 },
    ]
    : [
      { x: -258, y: -188 },
      { x: -54, y: -384 },
      { x: 238, y: -296 },
      { x: 454, y: -132 },
      { x: 524, y: 78 },
      { x: 352, y: 314 },
      { x: 92, y: 436 },
      { x: -186, y: 300 },
      { x: -396, y: 44 },
    ]
  const streamBlueprints = isMobile
    ? [
      { angle: -2.42, spread: 0.18, radius: 284, step: 92, skewX: -112, skewY: -62, stretchX: 1.12, stretchY: 0.9, phase: 0.2 },
      { angle: -0.9, spread: 0.22, radius: 344, step: 108, skewX: 62, skewY: -136, stretchX: 1.16, stretchY: 0.88, phase: 0.92 },
      { angle: -0.16, spread: 0.18, radius: 456, step: 118, skewX: 218, skewY: -10, stretchX: 1.2, stretchY: 0.88, phase: 1.5 },
      { angle: 0.58, spread: 0.2, radius: 404, step: 110, skewX: 148, skewY: 104, stretchX: 1.18, stretchY: 0.9, phase: 2.16 },
      { angle: 1.18, spread: 0.18, radius: 314, step: 88, skewX: -6, skewY: 174, stretchX: 1.08, stretchY: 0.94, phase: 2.8 },
    ]
    : [
      { angle: -2.5, spread: 0.2, radius: 304, step: 112, skewX: -154, skewY: -84, stretchX: 1.18, stretchY: 0.86, phase: 0.18 },
      { angle: -0.96, spread: 0.24, radius: 380, step: 126, skewX: 84, skewY: -174, stretchX: 1.22, stretchY: 0.84, phase: 0.94 },
      { angle: -0.14, spread: 0.2, radius: 500, step: 142, skewX: 334, skewY: -16, stretchX: 1.24, stretchY: 0.86, phase: 1.56 },
      { angle: 0.5, spread: 0.22, radius: 452, step: 134, skewX: 232, skewY: 118, stretchX: 1.22, stretchY: 0.88, phase: 2.14 },
      { angle: 1.12, spread: 0.18, radius: 318, step: 104, skewX: 0, skewY: 236, stretchX: 1.12, stretchY: 0.94, phase: 2.76 },
    ]
  const streamOrder = isMobile
    ? [2, 3, 1, 4, 2, 0, 3, 1, 4]
    : [2, 3, 1, 4, 2, 3, 0, 1, 4, 2, 3, 0]
  const streamCounts = new Array(streamBlueprints.length).fill(0)
  let poetStreamCursor = 0
  const majorNodes = nodes
    .filter((node) => node.id !== centerNodeId && node.tier === 'major' && node.type !== 'category')
    .sort((left, right) => right.importance - left.importance)
  const majorIndexById = new Map(majorNodes.map((node, index) => [node.id, index]))

  nodes.forEach((node, index) => {
    if (node.id === centerNodeId) {
      node.x = centerX
      node.y = centerY
      node.targetX = node.x
      node.targetY = node.y
      return
    }

    if (node.tier === 'major' && node.type !== 'category') {
      const majorIndex = majorIndexById.get(node.id) ?? index
      const slot = majorOffsets[majorIndex] ?? majorOffsets[majorOffsets.length - 1]!
      const waveX = Math.sin((majorIndex + 1) * 0.66) * (isMobile ? 12 : 18)
      const waveY = Math.cos((majorIndex + 1) * 0.54) * (isMobile ? 10 : 16)

      node.x = centerX + slot.x + waveX + node.x * 0.08 + (random() - 0.5) * (isMobile ? 18 : 24)
      node.y = centerY + slot.y + waveY + node.y * 0.06 + (random() - 0.5) * (isMobile ? 12 : 18)
      node.depth = 0.88 + Math.max(0, 0.08 - majorIndex * 0.01)
      node.targetX = node.x
      node.targetY = node.y
      return
    }

    if (node.type === 'poet') {
      const streamIndex = streamOrder[poetStreamCursor % streamOrder.length]!
      poetStreamCursor += 1
      const stream = streamBlueprints[streamIndex]!
      const streamLane = streamCounts[streamIndex]++
      const laneRatio = streamLane / Math.max(Math.ceil(nodes.length / streamBlueprints.length), 1)
      const radius = stream.radius + streamLane * stream.step + random() * (isMobile ? 28 : 46)
      const angle = stream.angle
        + (random() - 0.5) * stream.spread
        + Math.sin((laneRatio + 0.16) * Math.PI * 1.48 + stream.phase) * 0.06

      node.x = centerX
        + Math.cos(angle) * radius * stream.stretchX
        + stream.skewX * (0.36 + laneRatio * 0.74)
        + Math.sin(laneRatio * Math.PI * 2.4 + stream.phase) * (isMobile ? 18 : 28)
        + node.x * 0.08
      node.y = centerY
        + Math.sin(angle) * radius * stream.stretchY
        + stream.skewY * (0.28 + laneRatio * 0.58)
        + Math.cos(laneRatio * Math.PI * 2 + stream.phase) * (isMobile ? 14 : 24)
        + node.y * 0.06
      node.depth = 0.28 + node.importance * 0.2 + Math.max(0, 0.08 - laneRatio * 0.12)
      node.targetX = node.x
      node.targetY = node.y
      return
    }

    const angle = Math.atan2(node.y, node.x)
    node.x = centerX + Math.cos(angle) * (isMobile ? 520 : 760) + node.x * 0.08 + (random() - 0.5) * 24
    node.y = centerY + Math.sin(angle) * (isMobile ? 280 : 360) + node.y * 0.06 + (random() - 0.5) * 20
    node.depth = node.type === 'dynasty'
      ? 0.46
      : 0.22 + node.importance * 0.12

    node.targetX = node.x
    node.targetY = node.y
  })
}

function compactDynastyCopy(value?: string) {
  if (!value) return undefined
  return value
    .replace(/^存世/, '')
    .replace(/^诗词/, '')
    .replace(/^诗歌/, '')
}

function dedupeEdges(edges: GraphRenderEdge[]) {
  const map = new Map<string, GraphRenderEdge>()
  edges.forEach((edge) => {
    const key = toPairKey(edge.sourceId, edge.targetId)
    const existing = map.get(key)
    if (!existing || existing.kind === 'ambient') {
      map.set(key, edge)
    }
  })
  return [...map.values()]
}

function createSignedCurve(index: number, minCurve: number, maxCurve: number) {
  const magnitude = minCurve + (index % 5) * ((maxCurve - minCurve) / 4)
  return index % 2 === 0 ? magnitude : -magnitude
}

function toPairKey(left: string, right: string) {
  return [left, right].sort().join('::')
}

function hashText(value: string) {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function createSeededRandom(seed: number) {
  let state = seed || 1
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0
    return state / 4294967296
  }
}
