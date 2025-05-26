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

// Proporção desejada para a viewport do canvas (ex: 4:3 como 800/600)
const TARGET_VIEWPORT_ASPECT_RATIO = (800 / 600); // ou 4 / 3

const viewportState = reactive({
  width: 800,  // Será atualizado dinamicamente
  height: 600, // Será atualizado dinamicamente
  scale: 1,
  offsetX: 0,
  offsetY: 0,
  isPanning: false,
  lastPanX: 0,
  lastPanY: 0,
});

const strokes = ref([]);
let currentStroke = null;

const drawingSettings = reactive({
  color: 'black',
  lineWidth: 3,
});

const menu = reactive({
  visible: false,
  x: 0,
  y: 0,
});

const longPressDuration = 1000; // ms para o toque longo
let longPressTimer = null;
let touchStartCoords = { x: 0, y: 0, time: 0 }; // Para detectar movimento e tempo do toque longo
const longPressMoveThreshold = 10; // Pixels que o dedo pode mover antes de cancelar o toque longo

let isMultiTouching = false;      // Flag para indicar se estamos em um gesto de múltiplos toques (pan/zoom)
let initialGestureInfo = {      // Para armazenar o estado inicial de um gesto de dois dedos
  pinchDistance: 0,
  midpoint: { x: 0, y: 0 },   // Ponto médio na tela
  worldMidpoint: { x: 0, y: 0}, // Ponto médio no mundo
  offsetX: 0,                 // viewportState.offsetX inicial
  offsetY: 0,                 // viewportState.offsetY inicial
  scale: 1,                   // viewportState.scale inicial
};

// --- Ciclo de Vida e Conexão Socket.IO ---
onMounted(() => {
  setupViewportAndWorld(); // Configura o tamanho inicial e a visualização
  window.addEventListener('resize', setupViewportAndWorld);

  // Conectar ao servidor Socket.IO
	const backendUrl = 'https://project3-2025a-gabriel.onrender.com';
	socket.value = io(backendUrl, {
	  transports: ['websocket', 'polling']
	});

  socket.value.on('connect', () => {
    console.log('Conectado ao servidor Socket.IO com ID:', socket.value.id);
  });

  socket.value.on('connection_established', (data) => {
    console.log(data.message, 'SID do servidor:', data.sid);
  });

  socket.value.on('disconnect', () => {
    console.log('Desconectado do servidor Socket.IO');
  });

  // Ouvir por traços iniciais ao conectar
  socket.value.on('initial_drawing', (data) => {
    console.log('Recebendo desenho inicial:', data.strokes.length, 'traços');
    strokes.value = data.strokes.map(strokeData => {
      // Garantir que a espessura seja tratada como espessura do mundo
      return {
        points: strokeData.points,
        color: strokeData.color,
        lineWidth: strokeData.lineWidth // Backend envia espessura do mundo
      };
    });
    redraw();
  });

  // Ouvir por novos traços de outros usuários
  socket.value.on('stroke_received', (strokeData) => {
    console.log('Novo traço recebido:', strokeData);
    // Adicionar o traço recebido à lista local
    // O backend já deve ter salvo e está apenas retransmitindo
    // A espessura da linha (lineWidth) já deve ser a espessura no "mundo"
    strokes.value.push({
      points: strokeData.points,
      color: strokeData.color,
      lineWidth: strokeData.lineWidth
    });
    redraw(); // Redesenha o canvas com o novo traço
  });

  // Ouvir por evento de limpar canvas
  socket.value.on('canvas_cleared', () => {
    console.log('Evento de limpar canvas recebido do servidor.');
    strokes.value = []; // Limpa os traços locais
    redraw();
  });
});

onUnmounted(() => {
  window.removeEventListener('resize', setupViewportAndWorld);
  if (socket.value) {
    socket.value.disconnect(); // Desconectar ao sair do componente
  }
});


// --- Inicialização, Redimensionamento e Redesenho ---

function setupViewportAndWorld() {
  const canvas = viewportCanvasRef.value;
  if (!canvas) return;

  // 1. Calcular dimensões da viewport mantendo a proporção
  const availableWidth = window.innerWidth;
  const availableHeight = window.innerHeight;

  let newViewportWidth = availableWidth;
  let newViewportHeight = availableWidth / TARGET_VIEWPORT_ASPECT_RATIO;

  if (newViewportHeight > availableHeight) {
    newViewportHeight = availableHeight;
    newViewportWidth = availableHeight * TARGET_VIEWPORT_ASPECT_RATIO;
  }

  // Aplicar um pequeno padding visual se desejar, ou usar 100%
  // Ex: Deixar 95% do espaço para ter uma pequena margem da borda da janela
  const paddingFactor = 1.0; // 1.0 para usar todo o espaço calculado
  viewportState.width = Math.floor(newViewportWidth * paddingFactor);
  viewportState.height = Math.floor(newViewportHeight * paddingFactor);

  // 2. Definir o tamanho do elemento canvas (viewport)
  canvas.width = viewportState.width;
  canvas.height = viewportState.height;

  // 3. Obter contexto
  ctx = canvas.getContext('2d');
  if (!ctx) return;

  // 4. Resetar a visualização do "mundo" dentro da nova viewport
  resetView();
}

function resetView() {
  if (!ctx) return; // Garante que o contexto exista
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

  // Limpa a viewport (com uma cor de fundo para a área fora do "mundo")
  ctx.fillStyle = '#777777'; 
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.save(); // Salva o estado do contexto da viewport (sem transformações)

  // Aplica a transformação da viewport (pan e zoom)
  ctx.translate(viewportState.offsetX, viewportState.offsetY);
  ctx.scale(viewportState.scale, viewportState.scale);

  // Desenha o fundo do "mundo"
  ctx.fillStyle = WORLD_BACKGROUND_COLOR;
  ctx.fillRect(0, 0, WORLD_WIDTH, WORLD_HEIGHT);

  // --- Início da Seção de Clipping ---
  ctx.save(); // Salva o estado do contexto transformado (antes de aplicar o clip)
  ctx.beginPath();
  ctx.rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT); // Define o retângulo do mundo como caminho
  ctx.clip(); // Define este caminho como a região de clipping

  // Desenha todos os traços armazenados (agora serão clipados)
  strokes.value.forEach(stroke => {
    if (stroke.points.length < 2) return;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.strokeStyle = stroke.color;
    ctx.lineWidth = stroke.lineWidth; // Esta já é a espessura ajustada para o "mundo"
    ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
    stroke.points.forEach(point => ctx.lineTo(point.x, point.y));
    ctx.stroke();
  });

  ctx.restore(); // Remove a região de clipping, restaurando para o estado transformado
  // --- Fim da Seção de Clipping ---

  ctx.restore(); // Restaura para o estado original da viewport (sem transformações)
}

onMounted(() => {
  setupViewportAndWorld(); // Configura o tamanho inicial e a visualização
  window.addEventListener('resize', setupViewportAndWorld); // Reconfigura no redimensionamento da janela
});

onUnmounted(() => {
  window.removeEventListener('resize', setupViewportAndWorld);
});


// --- Conversão de Coordenadas ---
function screenToWorldCoordinates(screenX, screenY) {
  return {
    x: (screenX - viewportState.offsetX) / viewportState.scale,
    y: (screenY - viewportState.offsetY) / viewportState.scale,
  };
}

// --- Manipuladores de Eventos de Desenho e Pan ---
function handleMouseDown(event) {
  menu.visible = false;
  const canvas = viewportCanvasRef.value;
  // Assegurar que o foco está no canvas para eventos de teclado, se necessário
  // canvas.focus(); // Adicione tabindex="0" ao canvas no template se usar foco

  if (event.button === 0) { // Botão esquerdo - Iniciar desenho
    const { x, y } = screenToWorldCoordinates(event.offsetX, event.offsetY);
	currentStroke = {
	  points: [{ x, y }], // x, y já estão em coordenadas do mundo
	  color: drawingSettings.color,
	  lineWidth: drawingSettings.lineWidth, // Usa diretamente a configuração, sem dividir pela escala
	};
    strokes.value.push(currentStroke);
    // Opcional: redesenhar imediatamente para ver o primeiro ponto
    // redraw();
  } else if (event.button === 1) { // Botão do meio (scroll click) - Iniciar Pan
    event.preventDefault();
    viewportState.isPanning = true;
    viewportState.lastPanX = event.clientX; // Usar clientX/Y para pan relativo à janela
    viewportState.lastPanY = event.clientY;
  }
}

function handleMouseMove(event) {
  if (currentStroke && (event.buttons & 1)) { // Desenhando com botão esquerdo pressionado
    const { x, y } = screenToWorldCoordinates(event.offsetX, event.offsetY);
    currentStroke.points.push({ x, y });
    redraw();
  } else if (viewportState.isPanning && (event.buttons & 4)) { // Pan com botão do meio pressionado
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
  if (event.button === 0 && currentStroke && currentStroke.points.length > 1) {
    // Emitir o traço completo para o servidor
    if (socket.value) {
      // currentStroke.lineWidth já é a espessura no "mundo"
      socket.value.emit('draw_stroke_event', {
        points: currentStroke.points,
        color: currentStroke.color,
        lineWidth: currentStroke.lineWidth
      });
    }
  }
  currentStroke = null; // Resetar o traço atual

  if (event.button === 1 || !(event.buttons & 4)) { // Pan
    viewportState.isPanning = false;
  }
}

// --- Manipulador de Zoom (Mouse Wheel) ---
function handleWheel(event) {
  event.preventDefault();
  const scaleAmountFactor = 1.1; // Fator de zoom mais suave
  const mouseX_view = event.offsetX;
  const mouseY_view = event.offsetY;

  const worldP_before = screenToWorldCoordinates(mouseX_view, mouseY_view);

  let newScale = viewportState.scale;
  if (event.deltaY < 0) { // Zoom In
    newScale *= scaleAmountFactor;
  } else { // Zoom Out
    newScale /= scaleAmountFactor;
  }
  // Limitar o zoom
  newScale = Math.max(0.05, Math.min(newScale, 20)); // Exemplo de limites

  viewportState.scale = newScale;

  viewportState.offsetX = mouseX_view - worldP_before.x * viewportState.scale;
  viewportState.offsetY = mouseY_view - worldP_before.y * viewportState.scale;

  redraw();
}

// --- Manipuladores de Toque ---
let touchCache = [];
const DOUBLE_TAP_THRESHOLD = 300;
let lastTapTime = 0;
let initialPinchDistance = 0; // Para pinch zoom
let initialTouchMidpoint = null; // Para two-finger pan

function getTouchMidpoint(t1, t2, rect) {
    return {
        x: (t1.clientX - rect.left + t2.clientX - rect.left) / 2,
        y: (t1.clientY - rect.top + t2.clientY - rect.top) / 2
    };
}

function showContextMenuAt(screenX, screenY) {
  // Cancela qualquer desenho em progresso se o menu de contexto for ativado
  if (currentStroke) {
    const index = strokes.value.indexOf(currentStroke);
    if (index > -1 && currentStroke.points.length <= 1) {
      // Se for apenas um ponto (toque sem arrastar significativo), remove da lista local
      // pois não será um traço válido para emitir.
      strokes.value.splice(index, 1);
    } else if (currentStroke.points.length > 1 && socket.value) {
      // Se já era um traço válido (mais de 1 ponto), emite para o servidor
      // antes de abrir o menu e cancelar o modo de desenho.
      socket.value.emit('draw_stroke_event', {
        points: currentStroke.points,
        color: currentStroke.color,
        lineWidth: currentStroke.lineWidth
      });
    }
    currentStroke = null; // Limpa o traço atual, já que o menu será aberto
    redraw(); // Atualiza o canvas se um traço de ponto único foi removido
  }
  isDrawing = false; // Garante que o modo de desenho seja desativado

  // Define a posição e visibilidade do menu
  menu.x = screenX;
  menu.y = screenY;
  menu.visible = true;
}

function handleTouchStart(event) {
  event.preventDefault(); // Prevenir comportamento padrão do navegador (scroll, zoom da página)
  menu.visible = false;   // Esconder menu de contexto se estiver visível
  const touches = event.touches;
  const rect = viewportCanvasRef.value.getBoundingClientRect();

  if (touches.length === 1) { // Um dedo tocando
    isMultiTouching = false;
    const touch = touches[0];
    touchStartCoords = { x: touch.clientX, y: touch.clientY, time: Date.now() };

    // Iniciar temporizador para toque longo (menu de contexto)
    clearTimeout(longPressTimer); // Limpar qualquer temporizador anterior
    longPressTimer = setTimeout(() => {
      // Verifica se o dedo não se moveu muito e ainda é um único toque
      const currentTime = Date.now();
      if (!isDrawing && !isMultiTouching && (currentTime - touchStartCoords.time) >= longPressDuration) {
        showContextMenuAt(touchStartCoords.x, touchStartCoords.y);
      }
      longPressTimer = null;
    }, longPressDuration);

    // Iniciar desenho
    const screenX = touch.clientX - rect.left;
    const screenY = touch.clientY - rect.top;
    const worldCoords = screenToWorldCoordinates(screenX, screenY);
    
    currentStroke = {
      points: [worldCoords],
      color: drawingSettings.color,
      lineWidth: drawingSettings.lineWidth, // Espessura no "mundo"
    };
    strokes.value.push(currentStroke); // Adiciona localmente para feedback imediato
    isDrawing = true;
    redraw(); // Redesenha para mostrar o primeiro ponto
  
  } else if (touches.length === 2) { // Dois dedos tocando: prepara para pan/zoom
    clearTimeout(longPressTimer); // Cancela o toque longo se o segundo dedo descer
    longPressTimer = null;
    isDrawing = false;          // Para de desenhar se estava com um dedo
    isMultiTouching = true;

    // Se havia um currentStroke de um dedo que acabou de se tornar um gesto de dois dedos,
    // finalize-o se for válido, ou remova-o se for apenas um ponto.
    if (currentStroke) {
        if (currentStroke.points.length > 1) {
            if (socket.value) {
                socket.value.emit('draw_stroke_event', {
                    points: currentStroke.points,
                    color: currentStroke.color,
                    lineWidth: currentStroke.lineWidth
                });
            }
        } else { // Apenas um ponto, remove
            const index = strokes.value.indexOf(currentStroke);
            if (index > -1) {
                strokes.value.splice(index, 1);
            }
        }
        currentStroke = null;
        redraw(); // Atualiza para remover/finalizar o traço anterior
    }


    const t1 = touches[0];
    const t2 = touches[1];

    initialGestureInfo.pinchDistance = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
    
    const screenMidX = (t1.clientX - rect.left + t2.clientX - rect.left) / 2;
    const screenMidY = (t1.clientY - rect.top + t2.clientY - rect.top) / 2;
    initialGestureInfo.midpoint = { x: screenMidX, y: screenMidY }; // Ponto médio na tela
    
    // Ponto no mundo que está sob o ponto médio dos dedos NO INÍCIO do gesto
    initialGestureInfo.worldMidpoint = screenToWorldCoordinates(screenMidX, screenY);
    
    initialGestureInfo.offsetX = viewportState.offsetX;
    initialGestureInfo.offsetY = viewportState.offsetY;
    initialGestureInfo.scale = viewportState.scale;
  }
}

function handleTouchMove(event) {
  event.preventDefault();
  const touches = event.touches;
  const rect = viewportCanvasRef.value.getBoundingClientRect();

  if (touches.length === 1 && !isMultiTouching) { // Mover com um dedo
    const touch = touches[0];
    const screenX = touch.clientX - rect.left;
    const screenY = touch.clientY - rect.top;

    // Se o temporizador de toque longo ainda estiver ativo, verifica se o dedo moveu demais
    if (longPressTimer) {
      const deltaX = touch.clientX - touchStartCoords.x;
      const deltaY = touch.clientY - touchStartCoords.y;
      if (Math.hypot(deltaX, deltaY) > longPressMoveThreshold) {
        clearTimeout(longPressTimer); // Cancela o toque longo
        longPressTimer = null;
      }
    }

    // Se estiver no modo de desenho e não esperando por toque longo
    if (isDrawing && currentStroke && !longPressTimer) {
      const worldCoords = screenToWorldCoordinates(screenX, screenY);
      currentStroke.points.push(worldCoords);
      redraw();
    }

  } else if (touches.length === 2 && isMultiTouching) { // Mover com dois dedos (pan/zoom)
    // Garante que o toque longo seja cancelado
    if (longPressTimer) {
        clearTimeout(longPressTimer);
        longPressTimer = null;
    }
    isDrawing = false; // Não está desenhando ao fazer gesto de pan/zoom

    const t1 = touches[0];
    const t2 = touches[1];

    const currentScreenMidX = (t1.clientX - rect.left + t2.clientX - rect.left) / 2;
    const currentScreenMidY = (t1.clientY - rect.top + t2.clientY - rect.top) / 2;
    
    // --- Pan ---
    // O pan é a diferença entre o ponto médio inicial dos dedos (em coordenadas de tela)
    // e o ponto médio atual, adicionado ao offset inicial da viewport.
    const deltaMidX = currentScreenMidX - initialGestureInfo.midpoint.x;
    const deltaMidY = currentScreenMidY - initialGestureInfo.midpoint.y;
    
    viewportState.offsetX = initialGestureInfo.offsetX + deltaMidX;
    viewportState.offsetY = initialGestureInfo.offsetY + deltaMidY;

    // --- Zoom (Pinch) ---
    const currentPinchDistance = Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
    let scaleFactor = 1;
    if (initialGestureInfo.pinchDistance > 0) { // Evita divisão por zero
      scaleFactor = currentPinchDistance / initialGestureInfo.pinchDistance;
    }
    
    let newScale = initialGestureInfo.scale * scaleFactor;
    newScale = Math.max(0.05, Math.min(newScale, 20)); // Limita o zoom

    // Para dar zoom em relação ao ponto médio dos dedos:
    // O ponto do "mundo" que estava sob o ponto médio inicial dos dedos
    // deve permanecer sob o ponto médio atual dos dedos após o novo zoom.
    viewportState.offsetX = currentScreenMidX - initialGestureInfo.worldMidpoint.x * newScale;
    viewportState.offsetY = currentScreenMidY - initialGestureInfo.worldMidpoint.y * newScale;
    viewportState.scale = newScale;

    redraw();
  }
}


function removeTouchFromCache(touchIdentifier) {
  const index = touchCache.findIndex(t => t.identifier === touchIdentifier);
  if (index !== -1) {
    touchCache.splice(index, 1);
  }
}

function handleTouchEnd(event) {
  event.preventDefault();
  clearTimeout(longPressTimer); // Sempre limpa o temporizador de toque longo
  longPressTimer = null;

  const touchesStillOnScreen = event.touches.length;

  // Se um traço estava sendo desenhado (isDrawing era true) e era um toque único
  if (isDrawing && currentStroke && !isMultiTouching) {
    if (currentStroke.points.length > 1) { // Só emite se for mais que um ponto
      if (socket.value) {
        socket.value.emit('draw_stroke_event', {
          points: currentStroke.points,
          color: currentStroke.color,
          lineWidth: currentStroke.lineWidth
        });
      }
    } else {
      // Se for apenas um ponto (clique/toque rápido sem mover), remove da lista local
      const index = strokes.value.indexOf(currentStroke);
      if (index > -1) {
        strokes.value.splice(index, 1);
      }
      redraw(); // Para limpar o ponto único da tela
    }
  }

  // Reseta o estado de desenho/gesto se não houver mais dedos ou se voltar para um dedo
  if (touchesStillOnScreen < 2) {
    isMultiTouching = false;
    // Se ainda houver um dedo, e não estávamos fazendo multi-touch,
    // o próximo touchstart tratará como um novo toque único.
  }
  if (touchesStillOnScreen < 1) {
    isDrawing = false;
    currentStroke = null;
  }
  // Se estávamos em multi-touch e agora temos 1 dedo, o próximo touchstart/move de 1 dedo reiniciará.
  // Ou, se estávamos em multi-touch e agora temos 0 dedos, tudo é resetado.
}

// --- Funções do Menu de Contexto ---
function showContextMenu(event) {
  menu.x = event.clientX;
  menu.y = event.clientY;
  menu.visible = true;
}

function clearStrokes() {
  strokes.value = [];
  redraw();
}

function handleMenuSelection(action, value) {
  menu.visible = false; // Esconde o menu após a seleção
  switch (action) {
    case 'clear':
      // Limpa localmente e emite para o servidor
      strokes.value = [];
      redraw();
      if (socket.value) {
        socket.value.emit('clear_canvas_event', {}); // Envia objeto vazio ou ID do quadro
      }
      break;
    case 'setColor':
      drawingSettings.color = value;
      break;
    case 'setThickness':
      drawingSettings.lineWidth = value; // Este é o novo valor para espessura no mundo
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