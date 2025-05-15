<script lang="ts">
  import { _ } from 'svelte-i18n';
  import {
    selectedBoundaryMap,
    selectedCoordinates,
    selectedDistrict
  } from '../../stores';
  import DefaultDetails from './DefaultDetails.svelte';
  import BoundaryDetails from './BoundaryDetails.svelte';
  import DistrictDetails from './DistrictDetails.svelte';
  import CoordinateDetails from './CoordinateDetails.svelte';
</script>

<nav
  id="sidebar"
  class="w-full h-1/2 md:h-full md:w-1/4 2xl:w-1/5 overflow-auto shadow-lg text-gray-900 dark:bg-neutral-900 dark:text-gray-100 flex flex-col"
>
  <div class="flex-1">
    {#if $selectedBoundaryMap && $selectedDistrict}
      <DistrictDetails />
    {:else if $selectedBoundaryMap && !$selectedDistrict}
      <BoundaryDetails />
    {:else if $selectedCoordinates}
      <CoordinateDetails />
    {:else}
      <DefaultDetails />
    {/if}
  </div>
  <footer class="p-4 dark:bg-neutral-900 flex content-start">
  </footer>
</nav>
