<template>
  <div
    class="context-menu"
    :style="{ top: y + 'px', left: x + 'px' }"
    @click.stop >
    <ul>
      <li @click="emitSelection('clear')">Limpar Canvas</li>
      <li class="separator">Cores</li>
      <li class="color-palette">
        <span
          v-for="color in palette"
          :key="color"
          :style="{ backgroundColor: color }"
          class="color-swatch"
          @click="emitSelection('setColor', color)"
        ></span>
      </li>
      <li class="separator">Espessura</li>
      <li class="thickness-options">
        <button @click="emitSelection('setThickness', 2)">Fina</button>
        <button @click="emitSelection('setThickness', 5)">Média</button>
        <button @click="emitSelection('setThickness', 10)">Grossa</button>
        <button @click="emitSelection('setThickness', 20)">Extra Grossa</button>
      </li>
	   <li @click="emitSelection('clear')">Limpar Desenho</li>
		<li @click="emitSelection('resetView')">Resetar Visualização</li> <li class="separator">Cores</li>
    </ul>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';

defineProps({
  x: Number,
  y: Number,
  // visible: Boolean // não é mais necessário como prop, controlado pelo v-if no pai
});

const emit = defineEmits(['select']);

const palette = [
  '#000000', '#FFFFFF', '#EF5350', '#FFCA28', // Preto, Branco, Vermelho Suave, Âmbar
  '#66BB6A', '#42A5F5', '#AB47BC', '#78909C', // Verde Suave, Azul Suave, Roxo Suave, Cinza Azulado
  '#EC407A', '#FFEE58', '#9CCC65', '#26C6DA', // Rosa, Amarelo Limão, Verde Lima, Ciano Suave
  '#FFA726', '#8D6E63', '#BDBDBD', '#546E7A', // Laranja Suave, Marrom Claro, Cinza Claro, Ardósia Escuro
];


const thicknessOptions = [
    { label: 'Fina', value: 2},
    { label: 'Média', value: 5},
    { label: 'Grossa', value: 10},
    { label: 'Extra Grossa', value: 20},
]

function emitSelection(action, value = null) {
  emit('select', action, value);
}
</script>

<style scoped>
.context-menu {
  position: fixed; /* Ou absolute, dependendo do container pai */
  background-color: white;
  border: 1px solid #ccc;
  box-shadow: 2px 2px 5px rgba(0,0,0,0.15);
  z-index: 1000;
  min-width: 180px;
}

.context-menu ul {
  list-style: none;
  padding: 5px 0;
  margin: 0;
  color: #333333; /* <<<<<< ADICIONE OU MODIFIQUE ESTA LINHA */
}

.context-menu li {
  padding: 8px 15px;
  cursor: pointer;
  /* A cor será herdada do 'ul' ou pode ser definida aqui também se necessário. */
}

.context-menu li:hover {
  background-color: #f0f0f0;
}

.context-menu li.separator {
  font-size: 0.8em;
  font-weight: bold;
  color: #555; /* Mantém um cinza um pouco mais claro para o separador ou mude para #333 */
  padding-top: 10px;
  padding-bottom: 5px;
  border-top: 1px solid #eee;
  cursor: default;
}
 .context-menu li.separator:hover {
     background-color: transparent;
 }

.color-palette {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* 4 cores por linha */
  gap: 4px;
  padding: 5px 10px !important; /* Sobrescreve o padding do li */
}
 .color-palette:hover { /* Para não ter hover no container da paleta */
     background-color: transparent !important;
 }

.color-swatch {
  width: 20px;
  height: 20px;
  border: 1px solid #eee;
  display: inline-block;
  cursor: pointer;
  border-radius: 3px;
}
.color-swatch:hover {
    border-color: #888;
    transform: scale(1.1);
}

.thickness-options {
  display: flex;
  justify-content: space-around;
  padding: 5px 10px !important;
}
 .thickness-options:hover {
     background-color: transparent !important;
 }

.thickness-options button {
  padding: 4px 8px;
  font-size: 0.9em;
  border: 1px solid #ddd;
  background-color: #fff;
  cursor: pointer;
  border-radius: 3px;
}
.thickness-options button:hover {
  background-color: #e9e9e9;
  border-color: #bbb;
}
</style>