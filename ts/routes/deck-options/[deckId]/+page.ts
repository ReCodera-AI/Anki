// Copyright: Anki Software, LLC and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import { getDeckConfigsForUpdate } from "@generated/backend";
import { getColConfig } from "@tslib/profile";

import { DeckOptionsState } from "../lib";
import type { PageLoad } from "./$types";

export const load = (async ({ params }) => {
    const deckId = Number(params.deckId);

    const did = BigInt(deckId);
    const [info, sortFieldOptions] = await Promise.all([
        getDeckConfigsForUpdate({ did }),
        getColConfig(`_deck_${did}_sortField`),
    ]);
    const stored = sortFieldOptions as { mode?: string; locale?: string } | null;
    const mode = ["automatic", "manual", "browser"].includes(stored?.mode ?? "")
        ? stored!.mode as "automatic" | "manual" | "browser"
        : "automatic";
    const state = new DeckOptionsState(BigInt(did), info, {
        mode,
        locale: stored?.locale ?? "",
    });

    return { state };
}) satisfies PageLoad;
