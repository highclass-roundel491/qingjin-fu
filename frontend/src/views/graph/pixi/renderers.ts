import { Container, Graphics } from 'pixi.js'
import { GRAPH_BACKGROUND, clamp, type EdgeAnchor, type GraphInteractionState, type GraphRenderNode, type GraphScene } from './types'

interface BackgroundParticle {
  x: number
  y: number
  radius: number
  alpha: number
  driftX: number
  driftY: number
  twinkle: number
  speed: number
  layer: 0 | 1 | 2
}

interface BackgroundNebula {
  x: number
  y: number
  radiusX: number
  radiusY: number
  alpha: number
  color: string
  phase: number
}

interface BackgroundFilament {
  start: Vector2
  controlA: Vector2
  controlB: Vector2
  end: Vector2
  alpha: number
  width: number
  color: string
  drift: number
  phase: number
}

export interface BackgroundField {
  width: number
  height: number
  particles: BackgroundParticle[]
  nebulae: BackgroundNebula[]
  filaments: BackgroundFilament[]
}

export interface NodeView {
  id: string
  container: Container
  outerGlow: Graphics
  corona: Graphics
  innerGlow: Graphics
  pulse: Graphics
  rays: Graphics
  core: Graphics
  ring: Graphics
  spark: Graphics
  x: number
  y: number
  targetX: number
  targetY: number
}

export interface EdgeCurve {
  id: string
  start: Vector2
  control: Vector2
  end: Vector2
  midpoint: Vector2
}

interface Vector2 {
  x: number
  y: number
}

export function createBackgroundField(key: string, width: number, height: number, density: number) {
  const random = createSeededRandom(hashText(`${key}:background`))
  const sceneIsAuthor = key.startsWith('level2:')
  const farCount = Math.round((sceneIsAuthor ? 228 : 180) * density)
  const midCount = Math.round((sceneIsAuthor ? 118 : 90) * density)
  const nearCount = Math.round((sceneIsAuthor ? 46 : 34) * density)
  const particles: BackgroundParticle[] = []

  for (let index = 0; index < farCount + midCount + nearCount; index += 1) {
    const layer: 0 | 1 | 2 = index < farCount ? 0 : index < farCount + midCount ? 1 : 2
    const radius = layer === 0
      ? 0.35 + random() * 0.7
      : layer === 1
        ? 0.5 + random() * 1.1
        : 0.9 + random() * 1.8

    particles.push({
      x: random() * width,
      y: random() * height,
      radius,
      alpha: layer === 0 ? 0.06 + random() * 0.08 : layer === 1 ? 0.12 + random() * 0.14 : 0.18 + random() * 0.22,
      driftX: (random() - 0.5) * (layer === 0 ? 0.012 : layer === 1 ? 0.025 : 0.045),
      driftY: (random() - 0.5) * (layer === 0 ? 0.012 : layer === 1 ? 0.025 : 0.045),
      twinkle: random() * Math.PI * 2,
      speed: 0.2 + random() * 0.45,
      layer,
    })
  }

  const nebulae: BackgroundNebula[] = [
    {
      x: width * 0.18,
      y: height * 0.26,
      radiusX: width * 0.24,
      radiusY: height * 0.18,
      alpha: 0.06,
      color: '#12263c',
      phase: 0.3,
    },
    {
      x: width * 0.78,
      y: height * 0.72,
      radiusX: width * 0.22,
      radiusY: height * 0.16,
      alpha: 0.055,
      color: '#2a2035',
      phase: 1.6,
    },
    {
      x: width * 0.56,
      y: height * 0.44,
      radiusX: width * 0.18,
      radiusY: height * 0.14,
      alpha: 0.045,
      color: '#3f3423',
      phase: 3.2,
    },
  ]

  const filamentCount = Math.max(sceneIsAuthor ? 12 : 8, Math.round((sceneIsAuthor ? 22 : 14) * density))
  const filaments: BackgroundFilament[] = Array.from({ length: filamentCount }, (_, index) => {
    const horizontal = index % 3 !== 0
    const start = {
      x: horizontal ? width * (-0.08 + random() * 0.18) : width * (0.22 + random() * 0.58),
      y: horizontal ? height * (0.12 + random() * 0.76) : height * (-0.08 + random() * 0.2),
    }
    const end = {
      x: horizontal ? width * (0.82 + random() * 0.22) : width * (0.16 + random() * 0.68),
      y: horizontal ? height * (0.08 + random() * 0.84) : height * (0.76 + random() * 0.22),
    }
    const sweep = horizontal ? height * (0.04 + random() * 0.12) : width * (0.05 + random() * 0.1)

    return {
      start,
      controlA: {
        x: horizontal ? width * (0.22 + random() * 0.18) : start.x + (random() - 0.5) * sweep,
        y: horizontal ? start.y + (random() - 0.5) * sweep : height * (0.24 + random() * 0.16),
      },
      controlB: {
        x: horizontal ? width * (0.58 + random() * 0.18) : end.x + (random() - 0.5) * sweep,
        y: horizontal ? end.y + (random() - 0.5) * sweep : height * (0.58 + random() * 0.18),
      },
      end,
      alpha: (sceneIsAuthor ? 0.014 : 0.012) + random() * (sceneIsAuthor ? 0.024 : 0.02),
      width: sceneIsAuthor ? 0.48 + random() * 0.82 : 0.4 + random() * 0.7,
      color: index % 4 === 0 ? '#e4d39c' : index % 4 === 1 ? '#b9d8ef' : index % 4 === 2 ? '#bfe9dc' : '#f2d9de',
      drift: (random() - 0.5) * 18,
      phase: random() * Math.PI * 2,
    } satisfies BackgroundFilament
  })

  return {
    width,
    height,
    particles,
    nebulae,
    filaments,
  } satisfies BackgroundField
}

export function resizeBackgroundField(field: BackgroundField, width: number, height: number) {
  const scaleX = width / Math.max(field.width, 1)
  const scaleY = height / Math.max(field.height, 1)

  field.width = width
  field.height = height

  field.particles.forEach((particle) => {
    particle.x *= scaleX
    particle.y *= scaleY
  })

  field.nebulae.forEach((nebula) => {
    nebula.x *= scaleX
    nebula.y *= scaleY
    nebula.radiusX *= scaleX
    nebula.radiusY *= scaleY
  })

  field.filaments.forEach((filament) => {
    filament.start.x *= scaleX
    filament.start.y *= scaleY
    filament.controlA.x *= scaleX
    filament.controlA.y *= scaleY
    filament.controlB.x *= scaleX
    filament.controlB.y *= scaleY
    filament.end.x *= scaleX
    filament.end.y *= scaleY
  })
}

export function drawBackground(graphics: Graphics, field: BackgroundField, elapsedSeconds: number) {
  graphics.clear()
  graphics.rect(0, 0, field.width, field.height).fill({ color: toPixiColor(GRAPH_BACKGROUND.base) })

  field.nebulae.forEach((nebula, index) => {
    const pulse = 0.86 + Math.sin(elapsedSeconds * 0.08 + nebula.phase + index) * 0.14
    const offsetX = Math.sin(elapsedSeconds * 0.03 + index) * 18
    const offsetY = Math.cos(elapsedSeconds * 0.025 + nebula.phase) * 16

    for (let layer = 0; layer < 7; layer += 1) {
      const ratio = 1 - layer / 7
      const alpha = nebula.alpha * pulse * ratio * ratio
      graphics
        .ellipse(
          nebula.x + offsetX * (1 - ratio),
          nebula.y + offsetY * (1 - ratio),
          nebula.radiusX * ratio,
          nebula.radiusY * ratio,
        )
        .fill({
          color: toPixiColor(nebula.color),
          alpha,
        })
    }
  })

  field.filaments.forEach((filament, index) => {
    const driftWave = Math.sin(elapsedSeconds * 0.04 + filament.phase) * filament.drift
    const alphaWave = 0.74 + Math.sin(elapsedSeconds * 0.08 + filament.phase + index * 0.2) * 0.26
    const startY = filament.start.y + driftWave * 0.2
    const controlAY = filament.controlA.y + driftWave * 0.6
    const controlBY = filament.controlB.y - driftWave * 0.5
    const endY = filament.end.y - driftWave * 0.15

    graphics
      .moveTo(filament.start.x, startY)
      .bezierCurveTo(
        filament.controlA.x,
        controlAY,
        filament.controlB.x,
        controlBY,
        filament.end.x,
        endY,
      )
      .stroke({
        color: toPixiColor(mixHex(filament.color, '#ffffff', 0.14)),
        alpha: filament.alpha * alphaWave * 0.28,
        width: filament.width * 3.8,
        cap: 'round',
        join: 'round',
      })

    graphics
      .moveTo(filament.start.x, startY)
      .bezierCurveTo(
        filament.controlA.x,
        controlAY,
        filament.controlB.x,
        controlBY,
        filament.end.x,
        endY,
      )
      .stroke({
        color: toPixiColor(filament.color),
        alpha: filament.alpha * alphaWave,
        width: filament.width,
        cap: 'round',
        join: 'round',
      })

    graphics
      .moveTo(filament.start.x, startY)
      .bezierCurveTo(
        filament.controlA.x,
        controlAY,
        filament.controlB.x,
        controlBY,
        filament.end.x,
        endY,
      )
      .stroke({
        color: toPixiColor(mixHex(filament.color, '#fffaf0', 0.26)),
        alpha: filament.alpha * alphaWave * 0.5,
        width: Math.max(filament.width * 0.32, 0.18),
        cap: 'round',
        join: 'round',
      })
  })

  field.particles.forEach((particle) => {
    particle.twinkle += particle.speed * 0.01
    particle.x += particle.driftX
    particle.y += particle.driftY

    if (particle.x < -4) particle.x = field.width + 4
    if (particle.x > field.width + 4) particle.x = -4
    if (particle.y < -4) particle.y = field.height + 4
    if (particle.y > field.height + 4) particle.y = -4

    const shimmer = 0.7 + Math.sin(elapsedSeconds * particle.speed + particle.twinkle) * 0.3
    const alpha = particle.alpha * shimmer
    const baseColor = particle.layer === 0
      ? '#d6def0'
      : particle.layer === 1
        ? '#eef5ff'
        : '#fff8e7'

    if (particle.layer === 2) {
      graphics.circle(particle.x, particle.y, particle.radius * 3.4).fill({
        color: toPixiColor(baseColor),
        alpha: alpha * 0.18,
      })
    }

    graphics.circle(particle.x, particle.y, particle.radius).fill({
      color: toPixiColor(baseColor),
      alpha,
    })
  })
}

export function createNodeView(node: GraphRenderNode) {
  const container = new Container()
  const outerGlow = new Graphics()
  const corona = new Graphics()
  const innerGlow = new Graphics()
  const pulse = new Graphics()
  const rays = new Graphics()
  const core = new Graphics()
  const ring = new Graphics()
  const spark = new Graphics()

  outerGlow.blendMode = 'screen'
  corona.blendMode = 'screen'
  innerGlow.blendMode = 'screen'
  pulse.blendMode = 'screen'
  rays.blendMode = 'add'
  spark.blendMode = 'add'

  container.addChild(outerGlow, corona, innerGlow, pulse, rays, core, ring, spark)

  return {
    id: node.id,
    container,
    outerGlow,
    corona,
    innerGlow,
    pulse,
    rays,
    core,
    ring,
    spark,
    x: node.x,
    y: node.y,
    targetX: node.targetX,
    targetY: node.targetY,
  } satisfies NodeView
}

export function updateNodeView(
  view: NodeView,
  node: GraphRenderNode,
  interaction: GraphInteractionState,
  elapsedSeconds: number,
) {
  const hovered = interaction.hoveredNodeId === node.id
  const selected = interaction.selectedNodeId === node.id
  const hoveredOrSelected = hovered || selected
  const pulseWave = 0.5 + Math.sin(elapsedSeconds * (node.tier === 'core' ? 0.72 : 0.38) + node.importance * 4.8) * 0.5
  const hoverBoost = hovered ? 0.16 : 0
  const selectedBoost = selected ? 0.24 : 0
  const emphasis = 1 + hoverBoost + selectedBoost
  const coreColor = node.tier === 'core'
    ? mixHex(node.color, '#fff7d8', 0.18)
    : node.tier === 'major'
      ? mixHex(node.color, '#ffffff', 0.03)
      : mixHex(node.color, '#ffffff', 0.1)
  const haloColor = node.tier === 'major'
    ? mixHex(node.color, '#ffffff', 0.1)
    : mixHex(node.color, '#ffffff', 0.16)

  view.container.position.set(view.x, view.y)
  view.container.alpha = node.tier === 'minor' ? 0.96 : 1

  view.outerGlow.clear()
  view.outerGlow
    .circle(0, 0, node.radius * (node.tier === 'core' ? 2.42 : node.tier === 'major' ? 2.32 : 1.42) * (1 + pulseWave * 0.016))
    .fill({
      color: toPixiColor(node.color),
      alpha: (node.tier === 'core' ? 0.026 : node.tier === 'major' ? 0.072 : 0.022) * node.glow * emphasis,
    })

  view.corona.clear()
  if (node.tier === 'core') {
    drawCoreLensFlare(
      view.corona,
      node.radius,
      toPixiColor(mixHex(node.color, '#fff8d1', 0.34)),
      0.13 * emphasis,
      pulseWave,
    )
    view.corona
      .circle(0, 0, node.radius * 1.12 * (1 + pulseWave * 0.012))
      .fill({
        color: toPixiColor(mixHex(node.color, '#ffffff', 0.48)),
        alpha: 0.12 * emphasis,
      })
  }

  view.innerGlow.clear()
  view.innerGlow
    .circle(0, 0, node.radius * (node.tier === 'core' ? 1.34 : node.tier === 'major' ? 1.26 : 1.06) * (1 + pulseWave * 0.012))
    .fill({
      color: toPixiColor(haloColor),
      alpha: (node.tier === 'core' ? 0.12 : node.tier === 'major' ? 0.116 : 0.05) * emphasis,
    })

  view.pulse.clear()
  if (node.tier === 'core') {
    view.pulse
      .circle(0, 0, node.radius * 2.18 * (1 + pulseWave * 0.038))
      .stroke({
        color: toPixiColor(mixHex(node.color, '#ffffff', 0.32)),
        alpha: 0.06 * (0.72 + pulseWave * 0.28),
        width: 0.82,
      })
    view.pulse
      .circle(0, 0, node.radius * 3.12 * (1 + pulseWave * 0.03))
      .stroke({
        color: toPixiColor(mixHex(node.color, '#f5df94', 0.2)),
        alpha: 0.024 * (0.74 + pulseWave * 0.26),
        width: 0.62,
      })
  }

  view.rays.clear()
  if (node.tier === 'core') {
    drawRayBurst(
      view.rays,
      node.radius * 0.78,
      node.radius * 4.9,
      toPixiColor(mixHex(node.color, '#fff6cf', 0.3)),
      0.15 * emphasis,
      elapsedSeconds,
    )
  }

  view.core.clear()
  if (node.tier === 'core') {
    view.core
      .circle(0, 0, node.radius * 0.92)
      .fill({
        color: toPixiColor(mixHex(node.color, '#fff0ba', 0.2)),
        alpha: 0.98,
      })
    view.core
      .circle(0, 0, node.radius * 0.38)
      .fill({
        color: toPixiColor('#fffef4'),
        alpha: 0.98,
      })
    view.core
      .circle(0, 0, node.radius * 0.14)
      .fill({
        color: toPixiColor('#fff6d1'),
        alpha: 0.98,
      })
  } else {
    view.core.circle(0, 0, node.radius * (node.tier === 'minor' ? 0.92 : 1) * emphasis).fill({
      color: toPixiColor(coreColor),
      alpha: 0.98,
    })
  }

  view.ring.clear()
  if (node.tier === 'core') {
    view.ring.circle(0, 0, node.radius * 1.04).stroke({
      color: toPixiColor(mixHex(node.color, '#fff6cf', 0.48)),
      alpha: 0.14,
      width: 0.82,
    })
  } else if (node.tier === 'major') {
    view.ring.circle(0, 0, node.radius * 1.08).stroke({
      color: toPixiColor(mixHex(node.color, '#ffffff', 0.2)),
      alpha: hoveredOrSelected ? 0.3 : 0.09,
      width: hoveredOrSelected ? 1 : 0.72,
    })
    if (node.labelVisible || node.importance >= 0.72) {
      view.ring.circle(0, 0, node.radius * 1.42 * (1 + pulseWave * 0.008)).stroke({
        color: toPixiColor(mixHex(node.color, '#fff6dd', 0.16)),
        alpha: hoveredOrSelected ? 0.16 : 0.05,
        width: 0.48,
      })
    }
  } else if (hoveredOrSelected) {
    view.ring.circle(0, 0, node.radius * 1.15 * emphasis).stroke({
      color: toPixiColor(mixHex(node.color, '#ffffff', 0.35)),
      alpha: 0.26,
      width: hovered ? 0.96 : 0.82,
    })
  }

  view.spark.clear()
  if (hovered || selected || node.tier === 'core' || (node.tier === 'major' && (node.labelVisible || node.importance >= 0.76))) {
    const sparkRadius = node.radius * (node.tier === 'core' ? 2.5 : node.tier === 'major' ? 1.62 : 1.45)
    const sparkAlpha = (node.tier === 'core' ? 0.12 : node.tier === 'major' ? 0.062 : 0.05) + hoverBoost * 0.06 + selectedBoost * 0.04
    drawStarSpark(view.spark, sparkRadius, toPixiColor(mixHex(node.color, '#ffffff', 0.4)), sparkAlpha)
  }
}

export function drawEdges(options: {
  glowGraphics: Graphics
  coreGraphics: Graphics
  flowGraphics: Graphics
  scene: GraphScene
  nodePositions: Map<string, Vector2>
  interaction: GraphInteractionState
  elapsedSeconds: number
}) {
  const anchors: EdgeAnchor[] = []
  const curves = new Map<string, EdgeCurve>()

  options.glowGraphics.clear()
  options.coreGraphics.clear()
  options.flowGraphics.clear()

  options.scene.edges.forEach((edge, index) => {
    const source = options.nodePositions.get(edge.sourceId)
    const target = options.nodePositions.get(edge.targetId)
    if (!source || !target) return

    const curve = buildEdgeCurve(edge.id, source, target, edge.curve)
    curves.set(edge.id, curve)
    const edgeDistance = Math.max(Math.hypot(target.x - source.x, target.y - source.y), 1)
    const touchesCore = options.scene.centerNodeId !== undefined
      && (edge.sourceId === options.scene.centerNodeId || edge.targetId === options.scene.centerNodeId)

    const hovered = options.interaction.hoveredEdgeId === edge.id
    const adjacentToSelection = options.interaction.selectedNodeId !== null
      && (
        options.interaction.selectedNodeId === edge.sourceId
        || options.interaction.selectedNodeId === edge.targetId
      )

    const shimmer = 0.9 + Math.sin(options.elapsedSeconds * 0.24 + index * 0.63) * 0.1
    const alphaBoost = hovered ? 1.95 : adjacentToSelection ? 1.3 : 1
    const baseWidth = edge.kind === 'semantic'
      ? 0.36 + edge.emphasis * 0.32
      : edge.kind === 'structural'
        ? 0.18 + edge.emphasis * 0.14
        : 0.12 + edge.emphasis * 0.05
    const lineAlpha = clamp(
      edge.alpha * alphaBoost * shimmer,
      edge.kind === 'ambient' ? 0.012 : 0.015,
      hovered ? 0.42 : edge.kind === 'semantic' ? 0.18 : edge.kind === 'ambient' ? 0.09 : 0.11,
    )
    const glowAlpha = clamp(lineAlpha * edge.glowStrength * (edge.kind === 'ambient' ? 0.46 : 0.62), 0.006, edge.kind === 'ambient' ? 0.14 : 0.18)
    const color = edge.kind === 'semantic'
      ? GRAPH_BACKGROUND.edgeSemantic
      : edge.kind === 'structural'
        ? GRAPH_BACKGROUND.edgeStructural
        : GRAPH_BACKGROUND.edgeAmbient

    drawQuadraticStroke(options.glowGraphics, curve, {
      color: mixHex(color, '#ffffff', 0.16),
      alpha: glowAlpha,
      width: baseWidth * (edge.kind === 'semantic' ? 2.65 : 1.9),
    })

    if (touchesCore && edge.kind !== 'ambient') {
      drawEdgeBundle(options, curve, source, target, {
        color,
        alpha: lineAlpha,
        glowAlpha,
        width: baseWidth,
      })
    } else if (edge.kind === 'ambient' && edgeDistance > 420 && (edge.emphasis >= 0.12 || index % 2 === 0)) {
      drawEdgeBundle(options, curve, source, target, {
        color,
        alpha: lineAlpha * 0.46,
        glowAlpha: glowAlpha * 0.72,
        width: baseWidth * 0.72,
      })
    }

    drawQuadraticStroke(options.coreGraphics, curve, {
      color: mixHex(color, '#ffffff', hovered ? 0.36 : 0.12),
      alpha: lineAlpha,
      width: hovered ? baseWidth * 1.35 : baseWidth,
    })

    if (edge.flow && (edge.isSemantic || hovered)) {
      const flowCount = hovered ? 3 : 2
      for (let markerIndex = 0; markerIndex < flowCount; markerIndex += 1) {
        const t = (options.elapsedSeconds * 0.05 + markerIndex * 0.23 + index * 0.07) % 1
        const point = pointOnQuadratic(curve, t)
        options.flowGraphics.circle(point.x, point.y, hovered ? 1.5 : 1.1).fill({
          color: toPixiColor('#fff6de'),
          alpha: hovered ? 0.44 : 0.26,
        })
      }
    }

    if (hovered && edge.label) {
      anchors.push({
        id: edge.id,
        label: edge.label,
        x: curve.midpoint.x,
        y: curve.midpoint.y,
      })
    }
  })

  return { anchors, curves }
}

export function buildEdgeCurve(id: string, source: Vector2, target: Vector2, curveStrength: number) {
  const midX = (source.x + target.x) / 2
  const midY = (source.y + target.y) / 2
  const dx = target.x - source.x
  const dy = target.y - source.y
  const distance = Math.max(Math.hypot(dx, dy), 1)
  const normalX = -dy / distance
  const normalY = dx / distance
  const offset = distance * curveStrength
  const control = {
    x: midX + normalX * offset,
    y: midY + normalY * offset,
  }

  return {
    id,
    start: { x: source.x, y: source.y },
    control,
    end: { x: target.x, y: target.y },
    midpoint: pointOnQuadraticRaw(source, control, target, 0.5),
  } satisfies EdgeCurve
}

export function pointOnQuadratic(curve: EdgeCurve, t: number) {
  return pointOnQuadraticRaw(curve.start, curve.control, curve.end, t)
}

export function distanceToEdge(point: Vector2, curve: EdgeCurve) {
  let best = Number.POSITIVE_INFINITY
  let previous = curve.start

  for (let step = 1; step <= 18; step += 1) {
    const current = pointOnQuadratic(curve, step / 18)
    best = Math.min(best, distanceToSegment(point, previous, current))
    previous = current
  }

  return best
}

function drawQuadraticStroke(
  graphics: Graphics,
  curve: EdgeCurve,
  style: { color: string; alpha: number; width: number },
) {
  graphics
    .moveTo(curve.start.x, curve.start.y)
    .quadraticCurveTo(curve.control.x, curve.control.y, curve.end.x, curve.end.y)
    .stroke({
      color: toPixiColor(style.color),
      alpha: style.alpha,
      width: style.width,
      cap: 'round',
      join: 'round',
    })
}

function drawEdgeBundle(
  options: {
    glowGraphics: Graphics
    coreGraphics: Graphics
  },
  curve: EdgeCurve,
  source: Vector2,
  target: Vector2,
  style: { color: string; alpha: number; glowAlpha: number; width: number },
) {
  const dx = target.x - source.x
  const dy = target.y - source.y
  const distance = Math.max(Math.hypot(dx, dy), 1)
  const normalX = -dy / distance
  const normalY = dx / distance
  const strandOffset = clamp(distance * 0.016, 3.4, 9.6)

  for (const direction of [-1, 1] as const) {
    const shiftedCurve = offsetCurve(curve, normalX * strandOffset * direction, normalY * strandOffset * direction)

    drawQuadraticStroke(options.glowGraphics, shiftedCurve, {
      color: mixHex(style.color, '#fff7df', 0.18),
      alpha: style.glowAlpha * 0.58,
      width: style.width * 1.12,
    })

    drawQuadraticStroke(options.coreGraphics, shiftedCurve, {
      color: mixHex(style.color, '#fffef6', 0.22),
      alpha: style.alpha * 0.42,
      width: Math.max(style.width * 0.42, 0.12),
    })
  }
}

function drawCoreLensFlare(
  graphics: Graphics,
  radius: number,
  color: number,
  alpha: number,
  pulseWave: number,
) {
  const longAxis = radius * (3.4 + pulseWave * 0.08)
  const shortAxis = radius * (2.36 + pulseWave * 0.06)

  graphics.ellipse(0, 0, longAxis, radius * 0.24).fill({
    color,
    alpha: alpha * 0.34,
  })
  graphics.ellipse(0, 0, radius * 0.22, shortAxis).fill({
    color,
    alpha: alpha * 0.22,
  })

  graphics
    .moveTo(-longAxis * 1.12, 0)
    .lineTo(longAxis * 1.12, 0)
    .moveTo(0, -shortAxis * 1.04)
    .lineTo(0, shortAxis * 1.04)
    .moveTo(-radius * 1.56, -radius * 1.56)
    .lineTo(radius * 1.56, radius * 1.56)
    .moveTo(-radius * 1.56, radius * 1.56)
    .lineTo(radius * 1.56, -radius * 1.56)
    .stroke({
      color,
      alpha: alpha * 0.42,
      width: Math.max(radius * 0.08, 1.2),
      cap: 'round',
      join: 'round',
    })
}

function offsetCurve(curve: EdgeCurve, offsetX: number, offsetY: number) {
  return {
    id: `${curve.id}:${offsetX}:${offsetY}`,
    start: {
      x: curve.start.x + offsetX,
      y: curve.start.y + offsetY,
    },
    control: {
      x: curve.control.x + offsetX * 1.18,
      y: curve.control.y + offsetY * 1.18,
    },
    end: {
      x: curve.end.x + offsetX,
      y: curve.end.y + offsetY,
    },
    midpoint: {
      x: curve.midpoint.x + offsetX,
      y: curve.midpoint.y + offsetY,
    },
  } satisfies EdgeCurve
}

function drawStarSpark(graphics: Graphics, radius: number, color: number, alpha: number) {
  graphics
    .moveTo(-radius, 0)
    .lineTo(radius, 0)
    .moveTo(0, -radius)
    .lineTo(0, radius)
    .stroke({
      color,
      alpha,
      width: 0.7,
      cap: 'round',
      join: 'round',
    })
}

function drawRayBurst(
  graphics: Graphics,
  innerRadius: number,
  outerRadius: number,
  color: number,
  alpha: number,
  elapsedSeconds: number,
) {
  const rayCount = 28

  for (let index = 0; index < rayCount; index += 1) {
    const phase = elapsedSeconds * 0.12 + index * 0.62
    const angle = (Math.PI * 2 * index) / rayCount + Math.sin(phase) * 0.022
    const startRadius = innerRadius * (0.88 + (index % 3) * 0.04)
    const endRadius = outerRadius * (0.64 + (index % 5) * 0.08 + Math.sin(phase) * 0.02)
    const width = index % 4 === 0 ? 1.08 : index % 3 === 0 ? 0.72 : 0.34
    const rayAlpha = alpha * (index % 4 === 0 ? 0.9 : index % 3 === 0 ? 0.58 : 0.34)

    graphics
      .moveTo(Math.cos(angle) * startRadius, Math.sin(angle) * startRadius)
      .lineTo(Math.cos(angle) * endRadius, Math.sin(angle) * endRadius)
      .stroke({
        color,
        alpha: rayAlpha,
        width,
        cap: 'round',
        join: 'round',
      })
  }
}

function pointOnQuadraticRaw(start: Vector2, control: Vector2, end: Vector2, t: number) {
  const oneMinusT = 1 - t
  return {
    x: oneMinusT * oneMinusT * start.x + 2 * oneMinusT * t * control.x + t * t * end.x,
    y: oneMinusT * oneMinusT * start.y + 2 * oneMinusT * t * control.y + t * t * end.y,
  }
}

function distanceToSegment(point: Vector2, start: Vector2, end: Vector2) {
  const dx = end.x - start.x
  const dy = end.y - start.y
  const lengthSquared = dx * dx + dy * dy

  if (lengthSquared === 0) {
    return Math.hypot(point.x - start.x, point.y - start.y)
  }

  const projection = clamp(
    ((point.x - start.x) * dx + (point.y - start.y) * dy) / lengthSquared,
    0,
    1,
  )
  const projectedX = start.x + projection * dx
  const projectedY = start.y + projection * dy

  return Math.hypot(point.x - projectedX, point.y - projectedY)
}

function toPixiColor(color: string) {
  return Number.parseInt(color.replace('#', ''), 16)
}

function mixHex(colorA: string, colorB: string, amount: number) {
  const safeAmount = clamp(amount, 0, 1)
  const rgbA = hexToRgb(colorA)
  const rgbB = hexToRgb(colorB)

  return rgbToHex({
    r: Math.round(rgbA.r + (rgbB.r - rgbA.r) * safeAmount),
    g: Math.round(rgbA.g + (rgbB.g - rgbA.g) * safeAmount),
    b: Math.round(rgbA.b + (rgbB.b - rgbA.b) * safeAmount),
  })
}

function hexToRgb(hex: string) {
  const normalized = hex.replace('#', '')
  const safeHex = normalized.length === 3
    ? normalized
        .split('')
        .map((channel) => `${channel}${channel}`)
        .join('')
    : normalized

  return {
    r: Number.parseInt(safeHex.slice(0, 2), 16),
    g: Number.parseInt(safeHex.slice(2, 4), 16),
    b: Number.parseInt(safeHex.slice(4, 6), 16),
  }
}

function rgbToHex(rgb: { r: number; g: number; b: number }) {
  return `#${[rgb.r, rgb.g, rgb.b]
    .map((value) => clamp(Math.round(value), 0, 255).toString(16).padStart(2, '0'))
    .join('')}`
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
