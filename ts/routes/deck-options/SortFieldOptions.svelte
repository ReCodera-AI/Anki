<!--
Copyright: Anki Software, LLC and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import { getNotetypeNames } from "@generated/backend";
    import * as tr from "@generated/ftl";
    import { getColConfigOptional } from "@tslib/profile";
    import { get } from "svelte/store";
    import type { DeckOptionsState } from "./lib";

    export let state: DeckOptionsState;

    const sortFieldMode = state.sortFieldMode;
    const sortFieldLocale = state.sortFieldLocale;

    let noteTypes: { id: bigint; name: string }[] = [];
    let selectedNotetypeId = "";
    let notetypeLocale = "";

    getNotetypeNames({}).then((names) => {
        noteTypes = names.entries.map((entry) => ({
            id: entry.id,
            name: entry.name,
        }));
    });

    async function selectNotetype(id: string): Promise<void> {
        selectedNotetypeId = id;
        if (!id) {
            notetypeLocale = "";
            return;
        }
        const current = get(state.notetypeSortLocales)[id];
        notetypeLocale =
            current ??
            String((await getColConfigOptional(`_nt_${id}_sortFieldLocale`)) ?? "");
        state.setNotetypeSortLocale(id, notetypeLocale, current === undefined);
    }

    function updateNotetypeLocale(value: string): void {
        notetypeLocale = value;
        if (selectedNotetypeId) {
            state.setNotetypeSortLocale(selectedNotetypeId, value.trim());
        }
    }
</script>

<section aria-labelledby="sort-field-options-title">
    <h3 id="sort-field-options-title">{tr.deckConfigSortFieldLanguage()}</h3>
    <label for="sort-field-mode">{tr.deckConfigSortFieldMode()}</label>
    <select id="sort-field-mode" bind:value={$sortFieldMode}>
        <option value="automatic">{tr.deckConfigSortFieldAutomatic()}</option>
        <option value="manual">{tr.deckConfigSortFieldManual()}</option>
        <option value="browser">{tr.deckConfigSortFieldBrowser()}</option>
    </select>

    {#if $sortFieldMode === "manual"}
        <label for="sort-field-locale">{tr.deckConfigSortFieldLanguageTag()}</label>
        <input
            id="sort-field-locale"
            type="text"
            bind:value={$sortFieldLocale}
            placeholder="ru"
            autocomplete="off"
            dir="ltr"
        />
        <p>{tr.deckConfigSortFieldManualHint()}</p>
    {:else if $sortFieldMode === "browser"}
        <label for="sort-field-notetype">{tr.deckConfigSortFieldNotetype()}</label>
        <select
            id="sort-field-notetype"
            value={selectedNotetypeId}
            on:change={(event) =>
                selectNotetype((event.currentTarget as HTMLSelectElement).value)}
        >
            <option value="">{tr.deckConfigSortFieldChooseNotetype()}</option>
            {#each noteTypes as noteType (noteType.id)}
                <option value={noteType.id.toString()}>{noteType.name}</option>
            {/each}
        </select>
        {#if selectedNotetypeId}
            <label for="sort-field-notetype-locale">
                {tr.deckConfigSortFieldNotetypeLanguageTag()}
            </label>
            <input
                id="sort-field-notetype-locale"
                type="text"
                value={notetypeLocale}
                on:input={(event) =>
                    updateNotetypeLocale(
                        (event.currentTarget as HTMLInputElement).value,
                    )}
                placeholder={tr.deckConfigSortFieldNotetypePlaceholder()}
                autocomplete="off"
                dir="ltr"
            />
        {/if}
        <p>{tr.deckConfigSortFieldBrowserHint()}</p>
    {/if}
</section>

<style>
    section {
        display: grid;
        gap: 0.5rem;
    }

    p {
        margin: 0;
    }
</style>
