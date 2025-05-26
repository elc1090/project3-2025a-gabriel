<template>
  <canvas
    ref="viewportCanvasRef"
    @mousedown="handleMouseDown"
    @mousemove="handleMouseMove"
    @mouseup="handleMouseUpOrOut"
    @mouseout="handleMouseUpOrOut"
    @wheel.prevent="handleWheel"
    @touchstart.prevent="handleTouchStart"
    @touchmove.prevent="handleTouchMove"
    @touchend="handleTouchEnd"
    @contextmenu.prevent="showContextMenu"
    class="viewport-canvas"
  ></canvas>
  <ContextMenu
    v-if="menu.visible"
    :x="menu.x"
    :y="menu.y"
    @select="handleMenuSelection"
  />
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import ContextMenu from './ContextMenu.vue';
import { io } from 'socket.io-client';

const socket = ref(null);

const viewportCanvasRef = ref(null);
let ctx = null;

const WORLD_WIDTH = 1000;
const WORLD_HEIGHT = 1000;
const WORLD_BACKGROUND_COLOR = '#FFFFFF';
const TARGET_VIEWPORT_ASPECT_RATIO = (800 / 600);

const viewportState = reactive({
  width: 800,
  height: 600,
  scale: 1,
  offsetX: 0,
  offsetY: 0,
  isPanning: false,
  lastPanX: 0,
  lastPanY: 0,
});

const strokes = ref([]);
let currentStroke = null;
let isDrawing = false; // Adicionado para controlar o estado de desenho

const drawingSettings = reactive({
  color: 'black',
  lineWidth: 3,
});

const menu = reactive({
  visible: false,
  x: 0,
  y: 0,
});

const longPressDuration = 700; // ms para o toque longo (ajustei um pouco)
let longPressTimer = null;
let touchStartCoords = { x: 0, y: 0, time: 0 };
const longPressMoveThreshold = 10; // Pixels

let isMultiTouching = false;
let initialGestureInfo = {
  pinchDistance: 0,
  midpoint: { x: 0, y: 0 },
  worldMidpoint: { x: 0, y: 0},
  offsetX: 0,
  offsetY: 0,
  scale: 1,
};

// --- Ciclo de Vida e Conexão Socket.IO ---
onMounted(() => {
  setupViewportAndWorld();
  window.addEventListener('resize', setupViewportAndWorld);

  const backendUrl = 'https://project3-2025a-gabriel.onrender.com';
  socket.value = io(backendUrl, {
    transports: ['websocket', 'polling']
  });

  socket.value.on('connect', () => {
    console.log('FRONTEND: Conectado ao servidor Socket.IO com ID:', socket.value.id);
  });

  socket.value.on('connection_established', (data) => {
    console.log('FRONTEND: ' + data.message, 'SID do servidor:', data.sid);
  });

  socket.value.on('disconnect', () => {
    console.log('FRONTEND: Desconectado do servidor Socket.IO');
  });

  socket.value.on('initial_drawing', (data) => {
    console.log('FRONTEND: Recebendo desenho inicial:', data.strokes.length, 'traços');
    strokes.value = data.strokes.map(strokeData => ({
      points: strokeData.points,
      color: strokeData.color,
      lineWidth: strokeData.lineWidth
    }));
    redraw();
  });

  socket.value.on('stroke_received', (strokeData) => {
    console.log('FRONTEND: Novo traço recebido:', strokeData);
    strokes.value.push({
      points: strokeData.points,
      color: strokeData.color,
      lineWidth: strokeData.lineWidth
    });
    redraw();
  });

  socket.value.on('canvas_cleared', () => {
    console.log('FRONTEND: Evento de limpar canvas recebido do servidor.');
    strokes.value = [];
    redraw();
  });
});

onUnmounted(() => {
  window.removeEventListener('resize', setupViewportAndWorld);
  if (socket.value) {
    socket.value.disconnect();
  }
});

// --- Funções de Setup, Desenho e Coordenadas (sem alterações nas lógicas centrais) ---
function setupViewportAndWorld() {
  const canvas = viewportCanvasRef.value;
  if (!canvas) return;
  const availableWidth = window.innerWidth;
  const availableHeight = window.innerHeight;
  let newViewportWidth = availableWidth;
  let newViewportHeight = availableWidth / TARGET_VIEWPORT_ASPECT_RATIO;
  if (newViewportHeight > availableHeight) {
    newViewportHeight = availableHeight;
    newViewportWidth = availableHeight * TARGET_VIEWPORT_ASPECT_RATIO;
  }
  viewportState.width = Math.floor(newViewportWidth);
  viewportState.height = Math.floor(newViewportHeight);
  canvas.width = viewportState.width;
  canvas.height = viewportState.height;
  ctx = canvas.getContext('2d');
  if (!ctx) return;
  resetView();
}

function resetView() {
  if (!ctx) return;
  const scaleX = viewportState.width / WORLD_WIDTH;
  const scaleY = viewportState.height / WORLD_HEIGHT;
  viewportState.scale = Math.min(scaleX, scaleY) * 0.9;
  viewportState.offsetX = (viewportState.width - WORLD_WIDTH * viewportState.scale) / 2;
  viewportState.offsetY = (viewportState.height - WORLD_HEIGHT * viewportState.scale) / 2;
  redraw();
}

function redraw() {
  if (!ctx) return;
  const canvas = viewportCanvasRef.value;
  ctx.fillStyle = '#777777'; 
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(viewportState.offsetX, viewportState.offsetY);
  ctx.scale(viewportState.scale, viewportState.scale);
  ctx.fillStyle = WORLD_BACKGROUND_COLOR;
  ctx.fillRect(0, 0, WORLD_WIDTH, WORLD_HEIGHT);
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT); 
  ctx.clip(); 
  strokes.value.forEach(stroke => {
    if (stroke.points.length < 2) return;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.strokeStyle = stroke.color;
    ctx.lineWidth = stroke.lineWidth; 
    ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
    stroke.points.forEach(point => ctx.lineTo(point.x, point.y));
    ctx.stroke();
  });
  ctx.restore(); 
  ctx.restore(); 
}

function screenToWorldCoordinates(screenX, screenY) {
  return {
    x: (screenX - viewportState.offsetX) / viewportState.scale,
    y: (screenY - viewportState.offsetY) / viewportState.scale,
  };
}

// --- Manipuladores de Eventos de Mouse (mantidos como na sua versão) ---
function handleMouseDown(event) {
  menu.visible = false;
  isDrawing = false; // Resetar isDrawing para interações de mouse
  if (event.button === 0) {
    const { x, y } = screenToWorldCoordinates(event.offsetX, event.offsetY);
    currentStroke = {
      points: [{ x, y }],
      color: drawingSettings.color,
      lineWidth: drawingSettings.lineWidth,
    };
    strokes.value.push(currentStroke);
    isDrawing = true; // Mouse está desenhando
    redraw(); // Para mostrar o primeiro ponto do mouse
  } else if (event.button === 1) {
    event.preventDefault();
    viewportState.isPanning = true;
    viewportState.lastPanX = event.clientX;
    viewportState.lastPanY = event.clientY;
  }
}

function handleMouseMove(event) {
  if (isDrawing && currentStroke && (event.buttons & 1)) { // Verifica se o botão esquerdo está pressionado
    const { x, y } = screenToWorldCoordinates(event.offsetX, event.offsetY);
    currentStroke.points.push({ x, y });
    redraw();
  } else if (viewportState.isPanning && (event.buttons & 4)) {
    const dx = event.clientX - viewportState.lastPanX;
    const dy = event.clientY - viewportState.lastPanY;
    viewportState.offsetX += dx;
    viewportState.offsetY += dy;
    viewportState.lastPanX = event.clientX;
    viewportState.lastPanY = event.clientY;
    redraw();
  }
}

function handleMouseUpOrOut(event) {
  if (event.button === 0 && currentStroke) { // Se estava desenhando com o botão esquerdo
    if (currentStroke.points.length > 1 && socket.value) {
      socket.value.emit('draw_stroke_event', {
        points: currentStroke.points,
        color: currentStroke.color,
        lineWidth: currentStroke.lineWidth
      });
    } else if (currentStroke.points.length <= 1) { // Remove ponto único se não arrastou
        const index = strokes.value.indexOf(currentStroke);
        if (index > -1) strokes.value.splice(index,1);
        redraw();
    }
    isDrawing = false;
  }
  currentStroke = null; // Resetar sempre, independente do botão

  if (event.button === 1 || !(event.buttons & 4)) {
    viewportState.isPanning = false;
  }
}

function handleWheel(event) {
  event.preventDefault();
  menu.visible = false; // Opcional: fechar menu no zoom
  const scaleAmountFactor = 1.1;
  const mouseX_view = event.offsetX;
  const mouseY_view = event.offsetY;
  const worldP_before = screenToWorldCoordinates(mouseX_view, mouseY_view);
  let newScale = viewportState.scale;
  if (event.deltaY < 0) {
    newScale *= scaleAmountFactor;
  } else {
    newScale /= scaleAmountFactor;
  }
  newScale = Math.max(0.05, Math.min(newScale, 20));
  viewportState.scale = newScale;
  viewportState.offsetX = mouseX_view - worldP_before.x * viewportState.scale;
  viewportState.offsetY = mouseY_view - worldP_before.y * viewportState.scale;
  redraw();
}

// --- Manipuladores de Toque ATUALIZADOS COM DEPURAÇÃO DETALHADA ---

function showContextMenuAt(screenX, screenY) {
  if (socket.value) socket.value.emit('debug_touch_event', { type: 'showContextMenuAt_Triggered', screenX, screenY, sid: socket.value.id });
  if (currentStroke) {
    const index = strokes.value.indexOf(currentStroke);
    if (index > -1 && currentStroke.points.length <= 1) {
      strokes.value.splice(index, 1);
       if (socket.value) socket.value.emit('debug_touch_event', { type: 'showContextMenuAt_RemovedSingleDotStroke', sid: socket.value.id });
    } else if (currentStroke.points.length > 1 && socket.value) {
      socket.value.emit('draw_stroke_event', {
        points: currentStroke.points,
        color: currentStroke.color,
        lineWidth: currentStroke.lineWidth
      });
      if (socket.value) socket.value.emit('debug_touch_event', { type: 'showContextMenuAt_EmittedStroke', points: currentStroke.points.length, sid: socket.value.id });
    }
    currentStroke = null;
    redraw();
  }
  isDrawing = false;
  menu.x = screenX;
  menu.y = screenY;
  menu.visible = true;
}

function handleTouchStart(event) {
  event.preventDefault();
  const touches = event.touches;
  const rect = viewportCanvasRef.value.getBoundingClientRect();
  
  // Envia dados de debug para o backend
  if (socket.value) {
    const touchDataForDebug = Array.from(touches).map(t => ({ id: t.identifier, clientX: t.clientX, clientY: t.clientY }));
    socket.value.emit('debug_touch_event', {
      type: 'touchstart_ENTRY',
      touchesLength: touches.length,
      changedTouchesLength: event.changedTouches.length,
      touchData: touchDataForDebug,
      userAgent: navigator.userAgent,
      sid: socket.value.id
    });
  }

  menu.visible = false;
  isDrawing = false; // Resetar isDrawing no início de cada touchstart

  if (touches.length === 1) {
    isMultiTouching = false;
    const touch = touches[0];
    touchStartCoords = { x: touch.clientX, y: touch.clientY, time: Date.now() };

    clearTimeout(longPressTimer);
    longPressTimer = setTimeout(() => {
      const currentTime = Date.now();
      const timeElapsed = currentTime - touchStartCoords.time;
      // Verifica se o dedo ainda está na mesma posição aproximada (touchStartCoords é do início do toque)
      // O importante é que o *movimento* em handleTouchMove cancela o timer.
      // Aqui, só checamos se o timer de fato completou o tempo e se não estamos já em outro estado.
      if (!isDrawing && !isMultiTouching && timeElapsed >= longPressDuration) {
        if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchstart_LongPress_TimerFired', sid: socket.value.id });
        showContextMenuAt(touchStartCoords.x, touchStartCoords.y);
      } else {
        if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchstart_LongPress_TimerFired_ConditionsNotMet', isDrawing, isMultiTouching, timeElapsed, sid: socket.value.id });
      }
      longPressTimer = null;
    }, longPressDuration);

    const screenX = touch.clientX - rect.left;
    const screenY = touch.clientY - rect.top;
    const worldCoords = screenToWorldCoordinates(screenX, screenY);
    
    currentStroke = {
      points: [worldCoords],
      color: drawingSettings.color,
      lineWidth: drawingSettings.lineWidth,
    };
    strokes.value.push(currentStroke);
    isDrawing = true; // Definir que está desenhando

    if (socket.value) {
      socket.value.emit('debug_touch_event', {
        type: 'touchstart_SingleTouch_DrawingInitialized',
        isDrawing_state: isDrawing,
        currentStroke_points_length: currentStroke.points.length,
        worldX: worldCoords.x, worldY: worldCoords.y,
        sid: socket.value.id
      });
    }
    redraw();
  
  } else if (touches.length >= 2) {
    if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchstart_MultiTouch_Initiated', isDrawing_before: isDrawing, currentStroke_exists_before: !!currentStroke, sid: socket.value.id, touches: touches.length });
    clearTimeout(longPressTimer);
    longPressTimer = null;
    
    if (isDrawing && currentStroke) { // Se estava desenhando com um dedo
        if (currentStroke.points.length > 1) {
            if (socket.value) {
                socket.value.emit('draw_stroke_event', { points: currentStroke.points, color: currentStroke.color, lineWidth: currentStroke.lineWidth });
                socket.value.emit('debug_touch_event', { type: 'touchstart_MultiTouch_FinalizedPriorSingleStroke', sid: socket.value.id });
            }
        } else {
            const index = strokes.value.indexOf(currentStroke);
            if (index > -1) strokes.value.splice(index, 1);
            if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchstart_MultiTouch_RemovedPriorSingleDot', sid: socket.value.id });
        }
    }
    isDrawing = false; // Para de desenhar
    currentStroke = null; // Limpa o traço de um dedo
    isMultiTouching = true;

    const t1 = touches[0];
    const t2 = touches[1];
    initialGestureInfo.pinchDistance = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
    const screenMidX = (t1.clientX - rect.left + t2.clientX - rect.left) / 2;
    const screenMidY = (t1.clientY - rect.top + t2.clientY - rect.top) / 2;
    initialGestureInfo.midpoint = { x: screenMidX, y: screenMidY };
    initialGestureInfo.worldMidpoint = screenToWorldCoordinates(screenMidX, screenMidY); // Corrigido aqui
    initialGestureInfo.offsetX = viewportState.offsetX;
    initialGestureInfo.offsetY = viewportState.offsetY;
    initialGestureInfo.scale = viewportState.scale;
    redraw(); // Para caso um traço anterior tenha sido removido
  }
}

function handleTouchMove(event) {
  event.preventDefault();
  const touches = event.touches;
  const rect = viewportCanvasRef.value.getBoundingClientRect();

  if (socket.value && touches.length > 0) {
    const touchDataForDebug = Array.from(touches).map(t => ({ id: t.identifier, clientX: t.clientX, clientY: t.clientY }));
    socket.value.emit('debug_touch_event', {
      type: 'touchmove_ENTRY',
      touchesLength: touches.length,
      isDrawing_state: isDrawing,
      isMultiTouching_state: isMultiTouching,
      currentStroke_exists: !!currentStroke,
      longPressTimer_active: !!longPressTimer,
      sid: socket.value.id,
      touchData: touchDataForDebug
    });
  }

  if (touches.length === 1 && !isMultiTouching) {
    const touch = touches[0];
    const screenX = touch.clientX - rect.left;
    const screenY = touch.clientY - rect.top;

    if (longPressTimer) {
      const deltaX = touch.clientX - touchStartCoords.x;
      const deltaY = touch.clientY - touchStartCoords.y;
      if (Math.hypot(deltaX, deltaY) > longPressMoveThreshold) {
        if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchmove_SingleTouch_LongPressCancelledByMove', sid: socket.value.id });
        clearTimeout(longPressTimer);
        longPressTimer = null;
      }
    }

    // Permite desenhar se isDrawing é true, currentStroke existe, e
    // ou o longPressTimer foi cancelado/expirado, ou ainda não atingiu a duração do longPress.
    if (isDrawing && currentStroke && (!longPressTimer || (Date.now() - touchStartCoords.time < longPressDuration))) {
      const worldCoords = screenToWorldCoordinates(screenX, screenY);
      currentStroke.points.push(worldCoords);
      if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchmove_SingleTouch_PointAdded', points: currentStroke.points.length, sid: socket.value.id });
      redraw();
    } else if (touches.length === 1 && socket.value) { // Loga por que não desenhou
        socket.value.emit('debug_touch_event', {
            type: 'touchmove_SingleTouch_NoDrawConditionMet',
            isDrawing_state: isDrawing,
            currentStroke_exists: !!currentStroke,
            longPressTimer_active: !!longPressTimer,
            timeSinceTouchStart: Date.now() - touchStartCoords.time,
            longPressDuration: longPressDuration,
            sid: socket.value.id
        });
    }
  } else if (touches.length >= 2 && isMultiTouching) {
    if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchmove_MultiTouch_Processing', sid: socket.value.id, touches: touches.length });
    if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
    }
    isDrawing = false; 

    const t1 = touches[0];
    const t2 = touches[1];
    const currentScreenMidX = (t1.clientX - rect.left + t2.clientX - rect.left) / 2;
    const currentScreenMidY = (t1.clientY - rect.top + t2.clientY - rect.top) / 2;
    
    const currentPinchDistance = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
    let scaleFactor = 1;
    if (initialGestureInfo.pinchDistance > 0) {
      scaleFactor = currentPinchDistance / initialGestureInfo.pinchDistance;
    }
    let newScale = initialGestureInfo.scale * scaleFactor;
    newScale = Math.max(0.05, Math.min(newScale, 20));
    
    viewportState.scale = newScale; // Aplica a nova escala primeiro
    
    // O ponto do mundo que estava sob o ponto médio inicial dos dedos deve
    // agora estar sob o ponto médio ATUAL dos dedos.
    // offsetX_novo = midScreenX_atual - worldMidX_inicial * escala_nova
    viewportState.offsetX = currentScreenMidX - initialGestureInfo.worldMidpoint.x * newScale;
    viewportState.offsetY = currentScreenMidY - initialGestureInfo.worldMidpoint.y * newScale;
    
    redraw();
  }
}

function handleTouchEnd(event) {
  event.preventDefault();
  
  // Envia dados de debug para o backend
  if (socket.value) {
    const touchDataForDebug = Array.from(event.changedTouches).map(t => ({ id: t.identifier, clientX: t.clientX, clientY: t.clientY }));
    socket.value.emit('debug_touch_event', {
      type: 'touchend_ENTRY',
      touchesLength: event.touches.length, // Dedos que AINDA ESTÃO na tela
      changedTouchesLength: event.changedTouches.length, // Dedos que foram LEVANTADOS
      touchData: touchDataForDebug,
      isDrawing_state_before_logic: isDrawing,
      isMultiTouching_state_before_logic: isMultiTouching,
      currentStroke_exists_before_logic: !!currentStroke,
      sid: socket.value.id
    });
  }

  clearTimeout(longPressTimer);
  longPressTimer = null;

  if (isDrawing && currentStroke && !isMultiTouching) { // Estava desenhando com um dedo e esse dedo foi levantado
    if (currentStroke.points.length > 1) {
      if (socket.value) {
        socket.value.emit('draw_stroke_event', {
          points: currentStroke.points,
          color: currentStroke.color,
          lineWidth: currentStroke.lineWidth
        });
        if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchend_EmittedDrawEvent', points: currentStroke.points.length, sid: socket.value.id });
      }
    } else {
      const index = strokes.value.indexOf(currentStroke);
      if (index > -1) {
        strokes.value.splice(index, 1);
      }
      if (socket.value) socket.value.emit('debug_touch_event', { type: 'touchend_RemovedSingleDotStroke', sid: socket.value.id });
      redraw(); 
    }
  }
  
  // Resetar estados
  if (event.touches.length < 2) { // Se menos de dois dedos restantes
    isMultiTouching = false;
    if (socket.value && isMultiTouching) socket.value.emit('debug_touch_event', { type: 'touchend_Reset_isMultiTouching_to_false', sid: socket.value.id });
  }
  if (event.touches.length < 1) { // Se nenhum dedo restante
    isDrawing = false;
    if (socket.value && isDrawing) socket.value.emit('debug_touch_event', { type: 'touchend_Reset_isDrawing_to_false', sid: socket.value.id });
  }
  // currentStroke só deve ser resetado se o traço terminou ou foi invalidado.
  // Se ainda há toques (ex: um dedo levantou de um gesto de dois dedos), não necessariamente reseta currentStroke
  // a menos que isDrawing também se torne false.
  if (!isDrawing) {
      currentStroke = null;
  }
}


// --- Funções do Menu de Contexto (mantidas como na sua versão) ---
function showContextMenu(event) {
  menu.x = event.clientX;
  menu.y = event.clientY;
  menu.visible = true;
}

function clearStrokes() { // Renomeada para consistência, chamada pelo menu
  strokes.value = [];
  redraw();
  if (socket.value) { // Notificar o servidor sobre a limpeza
    socket.value.emit('clear_canvas_event', {});
  }
}

function handleMenuSelection(action, value) {
  menu.visible = false;
  switch (action) {
    case 'clear':
      clearStrokes(); // Chama a função de limpeza
      break;
    case 'setColor':
      drawingSettings.color = value;
      break;
    case 'setThickness':
      drawingSettings.lineWidth = value;
      break;
    case 'resetView':
      resetView();
      break;
  }
}
</script>

<style scoped>
.viewport-canvas {
  border: 1px solid #505050;
  cursor: crosshair;
  background-color: #777;
  display: block;
  touch-action: none;
  box-shadow: 0 0 10px rgba(0,0,0,0.3);
}
</style>