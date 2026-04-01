import { Application, Container, Graphics, Rectangle } from 'pixi.js'
import { Viewport } from 'pixi-viewport'
import { LabelOverlay } from './labelOverlay'
import {
  createBackgroundField,
  createNodeView,
  distanceToEdge,
  drawBackground,
  drawEdges,
  resizeBackgroundField,
  updateNodeView,
  type BackgroundField,
  type EdgeCurve,
  type NodeView,
} from './renderers'
import { clamp, type GraphInteractionState, type GraphRenderEdge, type GraphRenderNode, type GraphScene } from './types'

interface GraphStageOptions {
  host: HTMLElement
  labelHost: HTMLElement
  onNodeClick?: (node: GraphRenderNode) => void
  onEdgeClick?: (edge: GraphRenderEdge) => void
  onHoverChange?: (payload: { hoveredNodeId: string | null; hoveredEdgeId: string | null }) => void
}

interface PointerState {
  down: boolean
  startX: number
  startY: number
  moved: boolean
}

interface CameraTarget {
  x: number
  y: number
  scale: number
}

export class GraphStage {
  private readonly options: GraphStageOptions
  private readonly app = new Application()
  private readonly backgroundGraphics = new Graphics()
  private readonly edgeGlowGraphics = new Graphics()
  private readonly edgeCoreGraphics = new Graphics()
  private readonly edgeFlowGraphics = new Graphics()
  private readonly nodesLayer = new Container()
  private canvas: HTMLCanvasElement | null = null
  private readonly nodeViews = new Map<string, NodeView>()
  private readonly nodePositions = new Map<string, { x: number; y: number }>()
  private readonly pointer: PointerState = {
    down: false,
    startX: 0,
    startY: 0,
    moved: false,
  }
  private readonly interaction: GraphInteractionState = {
    hoveredNodeId: null,
    hoveredEdgeId: null,
    selectedNodeId: null,
  }

  private scene: GraphScene | null = null
  private labelOverlay: LabelOverlay | null = null
  private viewport: Viewport | null = null
  private backgroundField: BackgroundField | null = null
  private edgeCurves = new Map<string, EdgeCurve>()
  private cameraTarget: CameraTarget | null = null
  private width = 1
  private height = 1
  private elapsedSeconds = 0
  private destroyed = false
  private overlayDirty = true
  private lastViewportState = { x: 0, y: 0, scale: 1 }

  constructor(options: GraphStageOptions) {
    this.options = options
  }

  async init() {
    this.width = Math.max(this.options.host.clientWidth, 1)
    this.height = Math.max(this.options.host.clientHeight, 1)

    await this.app.init({
      width: this.width,
      height: this.height,
      antialias: true,
      autoDensity: true,
      resolution: window.devicePixelRatio || 1,
      backgroundAlpha: 0,
      preference: 'webgl',
    })

    this.canvas = this.app.canvas
    this.options.host.appendChild(this.canvas)
    this.canvas.className = 'graph-pixi-canvas'
    this.canvas.style.cursor = 'grab'
    this.canvas.addEventListener('pointerdown', this.handlePointerDown)
    this.canvas.addEventListener('pointermove', this.handlePointerMove)
    this.canvas.addEventListener('pointerup', this.handlePointerUp)
    this.canvas.addEventListener('pointerleave', this.handlePointerLeave)

    this.app.stage.addChild(this.backgroundGraphics)

    this.viewport = new Viewport({
      screenWidth: this.width,
      screenHeight: this.height,
      worldWidth: this.width,
      worldHeight: this.height,
      events: this.app.renderer.events,
      ticker: this.app.ticker,
    })
    this.viewport.drag().pinch().wheel({ smooth: 4 }).decelerate().clampZoom({
      minScale: 0.38,
      maxScale: 3.1,
    })
    this.app.stage.addChild(this.viewport)

    this.nodesLayer.sortableChildren = true
    this.edgeGlowGraphics.blendMode = 'screen'
    this.edgeFlowGraphics.blendMode = 'screen'
    this.viewport.addChild(this.edgeGlowGraphics, this.edgeCoreGraphics, this.edgeFlowGraphics, this.nodesLayer)

    this.labelOverlay = new LabelOverlay(this.options.labelHost)
    this.app.ticker.add(this.handleTick)
  }

  destroy() {
    if (this.destroyed) return
    this.destroyed = true

    this.app.ticker.remove(this.handleTick)
    this.canvas?.removeEventListener('pointerdown', this.handlePointerDown)
    this.canvas?.removeEventListener('pointermove', this.handlePointerMove)
    this.canvas?.removeEventListener('pointerup', this.handlePointerUp)
    this.canvas?.removeEventListener('pointerleave', this.handlePointerLeave)

    this.labelOverlay?.destroy()
    this.labelOverlay = null

    this.nodeViews.forEach((view) => {
      view.container.destroy({ children: true })
    })
    this.nodeViews.clear()
    this.edgeCurves.clear()
    this.nodePositions.clear()

    const initializedApp = (this.app as { renderer?: unknown }).renderer !== undefined
    if (initializedApp) {
      this.viewport?.destroy({ children: true })
      this.app.destroy({ removeView: false }, { children: true })
    }
    this.viewport = null

    if (this.canvas && this.canvas.parentElement === this.options.host) {
      this.options.host.removeChild(this.canvas)
    }
    this.canvas = null
  }

  resize(width: number, height: number) {
    this.width = Math.max(width, 1)
    this.height = Math.max(height, 1)

    this.app.renderer.resize(this.width, this.height)
    this.viewport?.resize(
      this.width,
      this.height,
      this.scene?.bounds.width ?? this.width,
      this.scene?.bounds.height ?? this.height,
    )

    if (this.backgroundField) {
      resizeBackgroundField(this.backgroundField, this.width, this.height)
    }

    if (this.scene) {
      this.fitScene(true)
    }

    this.overlayDirty = true
  }

  setScene(scene: GraphScene | null) {
    this.scene = scene
    this.overlayDirty = true
    this.interaction.hoveredNodeId = null
    this.interaction.hoveredEdgeId = null
    this.options.onHoverChange?.({
      hoveredNodeId: null,
      hoveredEdgeId: null,
    })

    if (!scene || !this.viewport) {
      this.clearSceneGraphics()
      return
    }

    this.backgroundField = createBackgroundField(scene.key, this.width, this.height, scene.particleDensity)
    this.viewport.resize(this.width, this.height, scene.bounds.width, scene.bounds.height)
    this.viewport.forceHitArea = new Rectangle(
      scene.bounds.minX,
      scene.bounds.minY,
      scene.bounds.width,
      scene.bounds.height,
    )

    const activeIds = new Set(scene.nodes.map((node) => node.id))

    this.nodeViews.forEach((view, id) => {
      if (activeIds.has(id)) return
      this.nodesLayer.removeChild(view.container)
      view.container.destroy({ children: true })
      this.nodeViews.delete(id)
      this.nodePositions.delete(id)
    })

    const fallbackOrigin = scene.centerNodeId
      ? this.nodeViews.get(scene.centerNodeId)
      : null

    scene.nodes.forEach((node) => {
      const existing = this.nodeViews.get(node.id)
      if (existing) {
        existing.targetX = node.targetX
        existing.targetY = node.targetY
        existing.container.zIndex = Math.round(node.depth * 100)
        return
      }

      const view = createNodeView(node)
      view.x = fallbackOrigin?.x ?? node.targetX
      view.y = fallbackOrigin?.y ?? node.targetY
      view.targetX = node.targetX
      view.targetY = node.targetY
      view.container.zIndex = Math.round(node.depth * 100)
      this.nodesLayer.addChild(view.container)
      this.nodeViews.set(node.id, view)
      this.nodePositions.set(node.id, { x: view.x, y: view.y })
    })

    this.fitScene(false)
  }

  setSelectedNode(nodeId: string | null) {
    this.interaction.selectedNodeId = nodeId
    this.overlayDirty = true
  }

  zoomIn() {
    if (!this.viewport) return
    const center = this.viewport.center
    this.queueCamera({
      x: center.x,
      y: center.y,
      scale: clamp(this.viewport.scale.x * 1.2, 0.38, 3.1),
    })
  }

  zoomOut() {
    if (!this.viewport) return
    const center = this.viewport.center
    this.queueCamera({
      x: center.x,
      y: center.y,
      scale: clamp(this.viewport.scale.x / 1.2, 0.38, 3.1),
    })
  }

  resetView() {
    this.fitScene(false)
  }

  focusNode(nodeId: string | null) {
    if (!nodeId || !this.scene || !this.viewport) return
    const node = this.scene.nodes.find((item) => item.id === nodeId)
    if (!node) return

    const fitScale = this.computeFitScale(this.scene)
    const targetScale = this.scene.level === 2
      ? clamp(
        node.tier === 'core'
          ? fitScale * 1.02
          : Math.max(fitScale * 1.12, fitScale + 0.08),
        0.34,
        node.tier === 'core' ? 0.98 : 1.08,
      )
      : clamp(
        node.tier === 'core'
          ? Math.max(fitScale * 1.06, fitScale + 0.04)
          : Math.max(fitScale * 1.16, fitScale + 0.12),
        0.42,
        1.4,
      )
    this.queueCamera({
      x: node.targetX,
      y: node.targetY,
      scale: targetScale,
    })
  }

  private clearSceneGraphics() {
    this.edgeGlowGraphics.clear()
    this.edgeCoreGraphics.clear()
    this.edgeFlowGraphics.clear()
    this.edgeCurves.clear()
  }

  private fitScene(immediate: boolean) {
    if (!this.scene) return

    const framingBounds = this.getFramingBounds(this.scene)
    const focusNode = this.scene.centerNodeId
      ? this.scene.nodes.find((node) => node.id === this.scene?.centerNodeId)
      : null
    const sceneCenterX = (framingBounds.minX + framingBounds.maxX) / 2
    const sceneCenterY = (framingBounds.minY + framingBounds.maxY) / 2
    const centerX = this.scene.level === 2 && focusNode
      ? lerp(sceneCenterX, focusNode.targetX, 0.66)
      : focusNode?.targetX ?? sceneCenterX
    const centerY = this.scene.level === 2 && focusNode
      ? lerp(sceneCenterY, focusNode.targetY, 0.6)
      : focusNode?.targetY ?? sceneCenterY
    const scale = this.computeFitScale(this.scene)

    this.queueCamera({ x: centerX, y: centerY, scale }, immediate)
  }

  private computeFitScale(scene: GraphScene) {
    const focusBounds = this.getFramingBounds(scene)
    const availableWidth = this.width * (scene.level === 2 ? 0.99 : 0.88)
    const availableHeight = this.height * (scene.level === 2 ? 0.95 : 0.86)
    const scale = Math.min(
      availableWidth / Math.max(focusBounds.maxX - focusBounds.minX, 1),
      availableHeight / Math.max(focusBounds.maxY - focusBounds.minY, 1),
    )
    const adjustedScale = scene.level === 2 ? scale * 1.1 : scale

    return clamp(
      adjustedScale,
      scene.level === 2 ? 0.34 : 0.56,
      scene.level === 2 ? 0.92 : scene.level === 1 ? 1.24 : 1.12,
    )
  }

  private getFramingBounds(scene: GraphScene) {
    if (scene.level === 2) return scene.bounds
    return this.getFocusBounds(scene)
  }

  private getFocusBounds(scene: GraphScene) {
    const focusNodes = scene.nodes.filter((node) => node.tier !== 'minor' || node.id === scene.centerNodeId)
    const sourceNodes = focusNodes.length > 0 ? focusNodes : scene.nodes
    const padding = scene.level === 2 ? 110 : 140

    return {
      minX: Math.min(...sourceNodes.map((node) => node.targetX - node.radius * 3)) - padding,
      minY: Math.min(...sourceNodes.map((node) => node.targetY - node.radius * 3)) - padding,
      maxX: Math.max(...sourceNodes.map((node) => node.targetX + node.radius * 3)) + padding,
      maxY: Math.max(...sourceNodes.map((node) => node.targetY + node.radius * 3)) + padding,
    }
  }

  private queueCamera(target: CameraTarget, immediate = false) {
    if (!this.viewport) return

    if (immediate) {
      this.viewport.setZoom(target.scale, true)
      this.viewport.moveCenter(target.x, target.y)
      this.cameraTarget = null
      this.overlayDirty = true
      return
    }

    this.cameraTarget = target
  }

  private updateCamera() {
    if (!this.viewport || !this.cameraTarget) return

    const currentCenter = this.viewport.center
    const currentScale = this.viewport.scale.x
    const nextX = lerp(currentCenter.x, this.cameraTarget.x, 0.14)
    const nextY = lerp(currentCenter.y, this.cameraTarget.y, 0.14)
    const nextScale = lerp(currentScale, this.cameraTarget.scale, 0.12)

    this.viewport.setZoom(nextScale, true)
    this.viewport.moveCenter(nextX, nextY)

    if (
      Math.abs(nextX - this.cameraTarget.x) < 0.45
      && Math.abs(nextY - this.cameraTarget.y) < 0.45
      && Math.abs(nextScale - this.cameraTarget.scale) < 0.002
    ) {
      this.viewport.setZoom(this.cameraTarget.scale, true)
      this.viewport.moveCenter(this.cameraTarget.x, this.cameraTarget.y)
      this.cameraTarget = null
    }
  }

  private renderScene() {
    if (!this.scene || !this.viewport) {
      this.clearSceneGraphics()
      return
    }

    const nodesById = new Map(this.scene.nodes.map((node) => [node.id, node]))
    let nodesMoving = false

    this.scene.nodes.forEach((node) => {
      const view = this.nodeViews.get(node.id)
      if (!view) return

      view.targetX = node.targetX
      view.targetY = node.targetY
      view.x = approach(view.x, view.targetX, 0.16)
      view.y = approach(view.y, view.targetY, 0.16)

      if (Math.abs(view.x - view.targetX) > 0.25 || Math.abs(view.y - view.targetY) > 0.25) {
        nodesMoving = true
      }

      this.nodePositions.set(node.id, { x: view.x, y: view.y })
      updateNodeView(view, node, this.interaction, this.elapsedSeconds)
    })

    const edgeResult = drawEdges({
      glowGraphics: this.edgeGlowGraphics,
      coreGraphics: this.edgeCoreGraphics,
      flowGraphics: this.edgeFlowGraphics,
      scene: this.scene,
      nodePositions: this.nodePositions,
      interaction: this.interaction,
      elapsedSeconds: this.elapsedSeconds,
    })

    this.edgeCurves = edgeResult.curves

    const viewportState = {
      x: this.viewport.position.x,
      y: this.viewport.position.y,
      scale: this.viewport.scale.x,
    }
    const viewportChanged = (
      Math.abs(viewportState.x - this.lastViewportState.x) > 0.4
      || Math.abs(viewportState.y - this.lastViewportState.y) > 0.4
      || Math.abs(viewportState.scale - this.lastViewportState.scale) > 0.001
    )
    this.lastViewportState = viewportState

    if (this.overlayDirty || nodesMoving || viewportChanged) {
      this.labelOverlay?.update(this.scene, this.viewport, this.nodePositions, {
        ...this.interaction,
        edgeAnchors: edgeResult.anchors,
      })
      this.overlayDirty = false
    }

    nodesById.forEach((node, id) => {
      const view = this.nodeViews.get(id)
      if (!view) return
      view.container.zIndex = Math.round(node.depth * 100)
    })
  }

  private readonly handleTick = () => {
    if (this.destroyed) return

    this.elapsedSeconds += this.app.ticker.deltaMS / 1000
    this.updateCamera()

    if (this.backgroundField) {
      drawBackground(this.backgroundGraphics, this.backgroundField, this.elapsedSeconds)
    }

    this.renderScene()
  }

  private readonly handlePointerDown = (event: PointerEvent) => {
    const point = this.toCanvasPoint(event)
    this.pointer.down = true
    this.pointer.startX = point.x
    this.pointer.startY = point.y
    this.pointer.moved = false
    if (this.canvas) this.canvas.style.cursor = 'grabbing'
  }

  private readonly handlePointerMove = (event: PointerEvent) => {
    if (!this.viewport || !this.scene) return

    const point = this.toCanvasPoint(event)
    if (this.pointer.down) {
      const distance = Math.hypot(point.x - this.pointer.startX, point.y - this.pointer.startY)
      if (distance > 6) {
        this.pointer.moved = true
        this.setHover(null, null)
        if (this.canvas) this.canvas.style.cursor = 'grabbing'
        return
      }
    }

    const worldPoint = this.viewport.toWorld(point)
    const node = this.findNodeAt(worldPoint)
    if (node) {
      this.setHover(node.id, null)
      if (this.canvas) this.canvas.style.cursor = 'pointer'
      return
    }

    const edge = this.findEdgeAt(worldPoint)
    if (edge) {
      this.setHover(null, edge.id)
      if (this.canvas) this.canvas.style.cursor = 'pointer'
      return
    }

    this.setHover(null, null)
    if (this.canvas) this.canvas.style.cursor = this.pointer.down ? 'grabbing' : 'grab'
  }

  private readonly handlePointerUp = (event: PointerEvent) => {
    if (!this.viewport || !this.scene) return

    const point = this.toCanvasPoint(event)
    const wasClick = this.pointer.down && !this.pointer.moved
    this.pointer.down = false
    if (this.canvas) this.canvas.style.cursor = 'grab'

    if (!wasClick) return

    const worldPoint = this.viewport.toWorld(point)
    const node = this.findNodeAt(worldPoint)
    if (node) {
      this.options.onNodeClick?.(node)
      return
    }

    const edge = this.findEdgeAt(worldPoint)
    if (edge?.isSemantic) {
      this.options.onEdgeClick?.(edge)
    }
  }

  private readonly handlePointerLeave = () => {
    this.pointer.down = false
    this.setHover(null, null)
    if (this.canvas) this.canvas.style.cursor = 'grab'
  }

  private findNodeAt(point: { x: number; y: number }) {
    if (!this.scene || !this.viewport) return null

    const threshold = 12 / Math.max(this.viewport.scale.x, 0.35)
    let match: GraphRenderNode | null = null
    let bestDistance = Number.POSITIVE_INFINITY

    for (const node of this.scene.nodes) {
      const position = this.nodePositions.get(node.id)
      if (!position) continue

      const distance = Math.hypot(point.x - position.x, point.y - position.y)
      const hitRadius = node.radius + threshold
      if (distance > hitRadius) continue

      const weightedDistance = distance - node.importance * 6 - (node.tier === 'core' ? 18 : 0)
      if (weightedDistance < bestDistance) {
        bestDistance = weightedDistance
        match = node
      }
    }

    return match
  }

  private findEdgeAt(point: { x: number; y: number }) {
    if (!this.scene || !this.viewport) return null

    const threshold = 14 / Math.max(this.viewport.scale.x, 0.4)
    let match: GraphRenderEdge | null = null
    let bestDistance = Number.POSITIVE_INFINITY

    for (const edge of this.scene.edges) {
      if (!edge.isSemantic) continue
      const curve = this.edgeCurves.get(edge.id)
      if (!curve) continue

      const distance = distanceToEdge(point, curve)
      if (distance > threshold) continue
      if (distance < bestDistance) {
        bestDistance = distance
        match = edge
      }
    }

    return match
  }

  private setHover(nodeId: string | null, edgeId: string | null) {
    if (
      this.interaction.hoveredNodeId === nodeId
      && this.interaction.hoveredEdgeId === edgeId
    ) {
      return
    }

    this.interaction.hoveredNodeId = nodeId
    this.interaction.hoveredEdgeId = edgeId
    this.overlayDirty = true
    this.options.onHoverChange?.({
      hoveredNodeId: nodeId,
      hoveredEdgeId: edgeId,
    })
  }

  private toCanvasPoint(event: PointerEvent) {
    const rect = this.canvas?.getBoundingClientRect()
    if (!rect) return { x: 0, y: 0 }
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    }
  }
}

function lerp(start: number, end: number, amount: number) {
  return start + (end - start) * amount
}

function approach(start: number, end: number, amount: number) {
  const next = lerp(start, end, amount)
  return Math.abs(next - end) < 0.01 ? end : next
}
