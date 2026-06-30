<template>
  <aside class="node-shelf" aria-labelledby="library-title">
    <div class="shelf-header">
      <h2 id="library-title">Nodes</h2>
      <input
        id="node-search"
        :value="nodeSearch"
        type="search"
        autocomplete="off"
        placeholder="Search nodes"
        @input="$emit('update:nodeSearch', $event.target.value)"
      >
      <div class="node-filters" aria-label="Node filters">
        <details id="node-filter-dropdown" class="filter-dropdown">
          <summary id="node-filter-summary">{{ nodeFilterSummary }}</summary>
          <section class="filter-section" data-filter-label="Package">
            <h3 id="package-filter-summary">Package</h3>
            <div id="package-filter-options" class="filter-options">
              <label v-for="value in filterOptionValues.package" :key="value" class="filter-option">
                <input :checked="selectedPackage.includes(value)" type="checkbox" :value="value" @change="toggleFilter('package', value, $event.target.checked)">
                <span>{{ value }}</span>
              </label>
            </div>
          </section>
          <section class="filter-section" data-filter-label="Input type">
            <h3 id="input-type-filter-summary">Input type</h3>
            <div id="input-type-filter-options" class="filter-options">
              <label v-for="value in filterOptionValues.input" :key="value" class="filter-option">
                <input :checked="selectedInputType.includes(value)" type="checkbox" :value="value" @change="toggleFilter('input', value, $event.target.checked)">
                <span>{{ value }}</span>
              </label>
            </div>
          </section>
          <section class="filter-section" data-filter-label="Output type">
            <h3 id="output-type-filter-summary">Output type</h3>
            <div id="output-type-filter-options" class="filter-options">
              <label v-for="value in filterOptionValues.output" :key="value" class="filter-option">
                <input :checked="selectedOutputType.includes(value)" type="checkbox" :value="value" @change="toggleFilter('output', value, $event.target.checked)">
                <span>{{ value }}</span>
              </label>
            </div>
          </section>
        </details>
      </div>
    </div>
    <div id="node-library" class="node-list">
      <section v-for="packageItem in filteredCatalog" :key="packageItem.id" class="node-package">
        <h3>{{ packageItem.title }}</h3>
        <p>{{ packageItem.description }}</p>
        <template v-for="item in packageItem.items" :key="`${packageItem.id}-${item.id || item.type}`">
          <CatalogGroup v-if="item.kind === 'group'" :item="item" :depth="0" @preview="(...args) => $emit('preview', ...args)" @move-preview="$emit('move-preview', $event)" @hide-preview="$emit('hide-preview')" />
          <NodeCard v-else-if="item.kind === 'node'" :node="item" @preview="(...args) => $emit('preview', ...args)" @move-preview="$emit('move-preview', $event)" @hide-preview="$emit('hide-preview')" />
        </template>
      </section>
    </div>
  </aside>
</template>

<script>
import CatalogGroup from "./CatalogGroup.vue";
import NodeCard from "./NodeCard.vue";

export default {
  name: "NodeShelf",
  components: {CatalogGroup, NodeCard},
  props: {
    filteredCatalog: {type: Array, required: true},
    filterOptionValues: {type: Object, required: true},
    nodeFilterSummary: {type: String, required: true},
    nodeSearch: {type: String, required: true},
    selectedInputType: {type: Array, required: true},
    selectedOutputType: {type: Array, required: true},
    selectedPackage: {type: Array, required: true},
  },
  emits: [
    "hide-preview",
    "move-preview",
    "preview",
    "update:nodeSearch",
    "update:selectedInputType",
    "update:selectedOutputType",
    "update:selectedPackage",
  ],
  methods: {
    toggleFilter(kind, value, checked) {
      const propByKind = {
        package: "selectedPackage",
        input: "selectedInputType",
        output: "selectedOutputType",
      };
      const eventByKind = {
        package: "update:selectedPackage",
        input: "update:selectedInputType",
        output: "update:selectedOutputType",
      };
      const current = this[propByKind[kind]];
      const next = checked ? [...current, value] : current.filter((item) => item !== value);
      this.$emit(eventByKind[kind], next);
    },
  },
};
</script>
