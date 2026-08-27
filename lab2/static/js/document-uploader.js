/**
 * Drag-and-drop, multi-file, live-preview receipt uploader. Shared by
 * report_form.html (new report) and report_detail.html (adding a
 * document to an existing draft) — same drop zone, same per-file tabs,
 * same "Detected: … / Defaulted, please check: …" preview note, so
 * attaching a receipt feels identical whether you're starting a report
 * or adding to one already in progress. Previously duplicated almost
 * verbatim between the two pages; extracted here so a fix or a new
 * field only has to happen once.
 *
 * initDocumentUploader(config) wires up one instance and returns
 * { getSelectedFiles(), clearFiles() } — what happens on submit (post
 * the whole page's form, vs. upload each file individually to an
 * existing report) is the caller's job, not this module's.
 */
function initDocumentUploader(config) {
    const filePicker = document.getElementById(config.filePickerId);
    const dropZone = document.getElementById(config.dropZoneId);
    const tabsList = document.getElementById(config.tabsListId);
    const panesContainer = document.getElementById(config.panesContainerId);
    const tabButtonTemplate = document.getElementById(config.tabButtonTemplateId);
    const paneTemplate = document.getElementById(config.paneTemplateId);
    const previewUrl = config.previewUrl;
    const csrfToken = config.csrfToken;
    const today = new Date().toISOString().slice(0, 10);

    // The single source of truth for what's attached — the native file
    // input can't accumulate across separate pick/drop interactions on
    // its own (every dialog selection, or every drop, replaces .files
    // wholesale), so every add/remove goes through this array first and
    // filePicker.files is rebuilt from it afterward, never the reverse.
    let selectedFiles = [];
    let objectUrls = [];
    let paneTooltips = [];

    function revokeObjectUrls() {
        objectUrls.forEach((url) => URL.revokeObjectURL(url));
        objectUrls = [];
    }

    function initTooltips(root) {
        if (typeof bootstrap === "undefined") return [];
        return Array.from(root.querySelectorAll('[data-bs-toggle="tooltip"]')).map(
            (el) => new bootstrap.Tooltip(el)
        );
    }

    function syncFilePickerInput() {
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach((file) => dataTransfer.items.add(file));
        filePicker.files = dataTransfer.files;
    }

    function addFiles(newFiles) {
        selectedFiles = selectedFiles.concat(Array.from(newFiles));
        syncFilePickerInput();
        rebuild(selectedFiles.length - 1);
    }

    function removeFileAt(index) {
        selectedFiles.splice(index, 1);
        syncFilePickerInput();
        rebuild(Math.min(index, selectedFiles.length - 1));
    }

    // Fires only on a genuine native-dialog pick (clicking the drop
    // zone label) — at that point filePicker.files is exactly the new
    // batch just chosen, appended to whatever was already attached.
    filePicker.addEventListener("change", () => addFiles(filePicker.files));

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("file-drop-zone-active");
        });
    });
    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("file-drop-zone-active");
        });
    });
    dropZone.addEventListener("drop", (event) => {
        if (!event.dataTransfer || !event.dataTransfer.files.length) return;
        addFiles(event.dataTransfer.files);
    });

    function activate(index) {
        tabsList.querySelectorAll(".document-tab-btn").forEach((btn, i) => {
            btn.classList.toggle("active", i === index);
        });
        panesContainer.querySelectorAll(".document-pane").forEach((pane, i) => {
            pane.hidden = i !== index;
        });
    }

    function buildPreview(file) {
        const wrap = document.createElement("div");
        const url = URL.createObjectURL(file);
        objectUrls.push(url);

        if (file.type.startsWith("image/")) {
            const img = document.createElement("img");
            img.src = url;
            img.className = "document-preview-img";
            img.alt = file.name;
            wrap.appendChild(img);
        } else {
            const embed = document.createElement("embed");
            embed.src = url;
            embed.type = "application/pdf";
            embed.className = "document-preview-pdf";
            wrap.appendChild(embed);
            const link = document.createElement("a");
            link.href = url;
            link.target = "_blank";
            link.rel = "noopener";
            link.className = "document-preview-open-link";
            link.textContent = "Open full size ↗";
            wrap.appendChild(link);
        }
        return wrap;
    }

    function rebuild(activeIndex) {
        revokeObjectUrls();
        paneTooltips.forEach((tooltip) => tooltip.dispose());
        paneTooltips = [];
        tabsList.innerHTML = "";
        panesContainer.innerHTML = "";

        selectedFiles.forEach((file, index) => {
            const tabButton = tabButtonTemplate.content.firstElementChild.cloneNode(true);
            tabButton.querySelector(".document-tab-icon").textContent = file.type.startsWith("image/") ? "🖼️" : "📄";
            tabButton.querySelector(".document-tab-label").textContent = file.name;
            tabButton.title = file.name;
            tabButton.addEventListener("click", () => activate(index));
            tabButton.querySelector(".document-tab-close").addEventListener("click", (event) => {
                event.stopPropagation();
                removeFileAt(index);
            });
            const tabItem = document.createElement("li");
            tabItem.className = "nav-item";
            tabItem.appendChild(tabButton);
            tabsList.appendChild(tabItem);

            const pane = paneTemplate.content.firstElementChild.cloneNode(true);
            pane.querySelector(".document-preview").appendChild(buildPreview(file));
            pane.querySelector(".doc-date").value = today;
            panesContainer.appendChild(pane);
            paneTooltips = paneTooltips.concat(initTooltips(pane));

            analyzeFile(file, pane);
        });

        if (config.onChange) config.onChange(selectedFiles);

        if (selectedFiles.length) {
            const clampedIndex = Math.max(0, Math.min(activeIndex, selectedFiles.length - 1));
            activate(clampedIndex);
        }
    }

    // Sends every PDF or photo to the same live-preview endpoint. A PDF
    // comes back with whatever text it could read (amount/type/date/
    // vendor/currency) to pre-fill the fields; a photo comes back with a
    // legibility check only (readable? sharp? real size?) — there's no
    // OCR of a photo, so its fields always need to be filled in by hand,
    // but a blurry/corrupt one is called out immediately either way.
    // Either way, the note sits *above* the fields and always separates
    // what was actually detected from what's just this form's default,
    // so a default never gets mistaken for a real reading off the file.
    function analyzeFile(file, pane) {
        const note = pane.querySelector(".preview-status-note");
        const isKnownType = /\.(pdf|jpe?g|png)$/i.test(file.name);

        if (!isKnownType) {
            note.textContent = "Unrecognized file type — every field below uses a default; please fill them in manually.";
            note.className = "preview-status-note preview-status-note-warning";
            return;
        }

        note.textContent = "Analyzing…";
        note.className = "preview-status-note preview-status-note-loading";

        const formData = new FormData();
        formData.append("file", file);

        fetch(previewUrl, { method: "POST", headers: { "X-CSRFToken": csrfToken }, body: formData })
            .then((response) => response.json())
            .then((data) => {
                if (data.is_image) {
                    applyImageAnalysis(data, note);
                } else {
                    applyPdfAnalysis(pane, data, note);
                }
            })
            .catch(() => {
                note.textContent = "Preview failed — enter every field manually, including the date/currency defaults.";
                note.className = "preview-status-note preview-status-note-warning";
            });
    }

    // Kept short on purpose — this appears after every single file, so it
    // only names *which* fields were detected vs. defaulted, not the
    // full sentence explaining why (that lives in the tooltips instead).
    function applyPdfAnalysis(pane, data, note) {
        const detected = [];
        const defaulted = [];

        if (data.extracted_amount) {
            pane.querySelector(".doc-amount").value = data.extracted_amount;
            detected.push("amount");
        } else {
            defaulted.push("amount");
        }

        if (data.detected_type) {
            pane.querySelector(".doc-type").value = data.detected_type;
            detected.push("type");
        } else {
            defaulted.push("type");
        }

        if (data.extracted_date) {
            pane.querySelector(".doc-date").value = data.extracted_date;
            detected.push("date");
        } else {
            defaulted.push("date");
        }

        if (data.extracted_vendor) {
            pane.querySelector(".doc-vendor").value = data.extracted_vendor;
            detected.push("vendor");
        } else {
            defaulted.push("vendor");
        }

        if (data.detected_currency) {
            pane.querySelector(".doc-currency").value = data.detected_currency;
            detected.push("currency");
        } else {
            defaulted.push("currency");
        }

        const parts = [];
        if (detected.length) parts.push("Detected: " + detected.join(", ") + ".");
        if (defaulted.length) parts.push("Defaulted, please check: " + defaulted.join(", ") + ".");

        note.textContent = parts.join(" ");
        note.className = detected.length
            ? "preview-status-note preview-status-note-success"
            : "preview-status-note preview-status-note-warning";
    }

    function applyImageAnalysis(data, note) {
        if (!data.image_is_readable) {
            note.textContent = "Couldn't read this file — every field below defaults, please fill in manually.";
            note.className = "preview-status-note preview-status-note-warning";
            return;
        }
        if (data.image_is_blurry) {
            note.textContent = "Looks blurry or too small — every field below defaults, please verify by eye.";
            note.className = "preview-status-note preview-status-note-warning";
            return;
        }
        note.textContent = "Photo looks clear, but can't be auto-read — every field below defaults, please fill in manually.";
        note.className = "preview-status-note preview-status-note-default";
    }

    return {
        getSelectedFiles: () => selectedFiles,
        getPane: (index) => panesContainer.querySelectorAll(".document-pane")[index],
        clearFiles: () => {
            selectedFiles = [];
            syncFilePickerInput();
            rebuild(0);
        },
    };
}
