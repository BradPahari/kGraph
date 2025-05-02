let filename = "";
let allEdges = [];
let allNodes = [];
let network = null;
let predicates = [];

async function loadPredicates() {
    try {
        const res = await fetch("/static/predicates.json");
        predicates = await res.json();
    } catch (err) {
        console.error("Failed to load predicates:", err);
        predicates = ["relatedTo"]; // fallback
    }
}

let selectedFiles = [];

function handleFileSelect() {
    const fileInput = document.getElementById("csvFile");
    const newFile = fileInput.files[fileInput.files.length - 1];
    if (!newFile || !newFile.name.endsWith(".csv")) return;

    // Prevent duplicates
    if (selectedFiles.some(f => f.name === newFile.name)) return;

    if (selectedFiles.length >= 5) {
        alert("You can only upload up to 5 files.");
        return;
    }

    selectedFiles.push(newFile);
    renderSelectedFiles();
    fileInput.value = ''; // clear input so same file can be reselected if deleted
}

function renderSelectedFiles() {
    const list = document.getElementById("selectedFilesList");
    list.innerHTML = selectedFiles.map((file, index) => `
                <div class="file-uploaded">
                    <div class="file-name">
                        <input type="checkbox" id="file-${index}" checked onchange="updateUploadButton()">
                        <i class="bi bi-file-earmark" style="font-size: 18px; color: #2563EB;"></i>
                        <span onclick="this.classList.toggle('expanded')" title="${file.name}">${file.name}</span>
                    </div>
                    <div class="file-actions">
                        <button onclick="document.getElementById('csvFile').click()">
                            <i class="bi bi-arrow-repeat" style="font-size: 18px; color: #2563EB;"></i>
                        </button>
                        <button onclick="removeFile(${index})">
                            <i class="bi bi-trash" style="font-size: 18px; color: #FF0000;"></i>
                        </button>
                    </div>
                </div>
            `).join('');
    updateUploadButton();
}

function updateUploadButton() {
    const uploadAllBtn = document.getElementById("uploadAllBtn");
    const checked = document.querySelectorAll('#selectedFilesList input[type="checkbox"]:checked');
    uploadAllBtn.disabled = checked.length === 0;
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderSelectedFiles();

    if (selectedFiles.length === 0) {
        // Clear file dropdowns
        document.getElementById("subjectFileSelect").innerHTML = "";
        document.getElementById("objectFileSelect").innerHTML = "";
        document.getElementById("subjectFileSelect").disabled = true;
        document.getElementById("objectFileSelect").disabled = true;

        // Clear column dropdowns
        document.getElementById("subjectSelect").innerHTML = "";
        document.getElementById("objectSelect").innerHTML = "";
        document.getElementById("subjectSelect").disabled = true;
        document.getElementById("objectSelect").disabled = true;

        // Disable buttons
        document.getElementById("generateBtn").disabled = true;
        document.getElementById("doneBtn").disabled = true;

        // Clear triple table
        document.getElementById("tripleTable").innerHTML = "";

        // Clear messages
        document.getElementById("messageBox").style.display = "none";
        document.getElementById("errorBox").style.display = "none";
    }
}


async function uploadCSV(files) {
    const subjectSel = document.getElementById("subjectSelect");
    const objectSel = document.getElementById("objectSelect");
    const generateBtn = document.getElementById("generateBtn");
    const doneBtn = document.getElementById("doneBtn");
    const messageBox = document.getElementById("messageBox");
    const errorBox = document.getElementById("errorBox");

    messageBox.style.display = "none";
    errorBox.style.display = "none";
    subjectSel.innerHTML = "";
    objectSel.innerHTML = "";
    subjectSel.disabled = true;
    objectSel.disabled = true;
    generateBtn.disabled = true;
    doneBtn.disabled = true;

    const formData = new FormData();
    const checkedBoxes = document.querySelectorAll('#selectedFilesList input[type="checkbox"]:checked');
    const checkedIndexes = Array.from(checkedBoxes).map(cb => parseInt(cb.id.replace('file-', '')));
    checkedIndexes.forEach(i => formData.append("files", selectedFiles[i]));

    try {
        const res = await fetch("/upload", {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Upload failed.");

        window.uploadedFileInfo = data.files;
        filename = data.files[0].filename;

        const subjectFileSelect = document.getElementById("subjectFileSelect");
        const objectFileSelect = document.getElementById("objectFileSelect");
        subjectFileSelect.innerHTML = "";
        objectFileSelect.innerHTML = "";

        data.files.forEach(file => {
            const shortName = file.filename.split("_").slice(1).join("_");
            const opt = `<option value="${file.filename}">${shortName}</option>`;
            subjectFileSelect.innerHTML += opt;
            objectFileSelect.innerHTML += opt;
        });

        // ✅ Enable the file dropdowns after upload
        subjectFileSelect.disabled = false;
        objectFileSelect.disabled = false;


        updateHeaderDropdowns();
        subjectSel.disabled = false;
        objectSel.disabled = false;
        generateBtn.disabled = false;
        messageBox.style.display = "block";
        messageBox.innerText = "Files uploaded successfully.";
    } catch (err) {
        errorBox.style.display = "block";
        errorBox.innerText = err.message || "An error occurred during upload.";
    }
}

async function generateTriples() {
    const subjectCol = document.getElementById("subjectSelect").value;
    const objectCol = document.getElementById("objectSelect").value;
    const subjectFile = document.getElementById("subjectFileSelect").value;
    const objectFile = document.getElementById("objectFileSelect").value;

    const res = await fetch("/prepare-triples", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            subject_file: subjectFile,
            object_file: objectFile,
            subject: subjectCol,
            object: objectCol
        })
    });
    const data = await res.json();
    if (!res.ok) {
        document.getElementById("errorBox").style.display = "block";
        document.getElementById("errorBox").innerText = data.error || "Triple prep failed.";
        return;
    }

    document.getElementById("doneBtn").disabled = false;
    document.getElementById("tripleTable").innerHTML =
        `<table><tr><th>Subject</th><th>Predicate</th><th>Object</th></tr>` +
        data.triples.map((t, i) => `
                    <tr>
                        <td>${t.subject}</td>
                        <td><select data-row="${i}">${predicates.map(p => `<option value="${p}">${p}</option>`).join("")}</select></td>
                        <td>${t.object}</td>
                    </tr>
                `).join("") +
        `</table>`;
}

async function submitTriples() {
    const selects = document.querySelectorAll("#tripleTable select");
    const triples = [];
    const subjectFile = document.getElementById("subjectFileSelect").value;
    const objectFile = document.getElementById("objectFileSelect").value;

    selects.forEach(sel => {
        const row = sel.closest("tr");
        triples.push({
            subject: row.children[0].innerText,
            predicate: sel.value,
            object: row.children[2].innerText,
            subjectFile,
            objectFile
        });
    });

    const res = await fetch("/build-graph", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            triples,
            filename
        })
    });
    const data = await res.json();
    allNodes = data.nodes;
    allEdges = data.edges;
    drawGraph(data);
    saveToLocalHistory({
        filename,
        triples,
        graphData: data
    });
    document.getElementById("saveAsBtn").disabled = false;
}

function cleanFilename(f) {
    return f.includes("_") ? f.split("_").slice(1).join("_") : f;
}

function drawGraph(graphData) {
    const container = document.getElementById("graph");
    const data = {
        nodes: new vis.DataSet(graphData.nodes),
        edges: new vis.DataSet(graphData.edges)
    };
    const options = {
        layout: {
            improvedLayout: true
        },
        physics: {
            stabilization: true,
            barnesHut: {
                gravitationalConstant: -5000,
                centralGravity: 0.3,
                springLength: 150,
                springConstant: 0.04
            }
        },
        edges: {
            arrows: "to"
        },
        interaction: {
            hover: true,
            tooltipDelay: 100,
            navigationButtons: true,
            selectable: true
        }
    };
    network = new vis.Network(container, data, options);

    network.on("click", function (params) {
        const infoBox = document.getElementById("infoBox");
        const nodeId = params.nodes[0];
        if (!nodeId) return (infoBox.innerText = "Click a node or edge to see more details.");

        const node = graphData.nodes.find(n => n.id === nodeId);
        const connected = graphData.edges.filter(e => e.from === nodeId || e.to === nodeId);

        const nodeFileMap = graphData.nodeSources || {};
        const nodeFile = cleanFilename(nodeFileMap[node.label] || 'unknown.csv');
        let desc = `Node: ${node.label} (${nodeFile})\nConnected to:\n`;
        connected.forEach(e => {
            const otherId = e.from === nodeId ? e.to : e.from;
            const otherLabel = graphData.nodes.find(n => n.id === otherId)?.label || "Unknown";
            const otherFile = cleanFilename(nodeFileMap[otherLabel] || 'unknown.csv');
            const direction = e.from === nodeId ? "→" : "←";
            desc += `• ${e.label} ${direction} ${otherLabel} (${otherFile})\n`;
        });

        infoBox.innerText = desc;

    });
}

function downloadGraphImage() {
    const canvas = document.querySelector("#graph canvas");
    const link = document.createElement("a");
    link.download = "knowledge_graph.png";
    link.href = canvas.toDataURL();
    link.click();
}

function saveToLocalHistory(entry) {
    const user = localStorage.getItem("currentUser") || "guest";
    const key = `kgraphHistory_${user}`;
    const history = JSON.parse(localStorage.getItem(key) || "[]");

    entry.id = Date.now();
    entry.timestamp = new Date().toISOString();
    entry.filename = cleanFilename(entry.filename || filename);
    history.push(entry);

    localStorage.setItem(key, JSON.stringify(history));
    populateHistoryList(); // refresh list for this user
}

function populateHistoryList() {
    const user = localStorage.getItem("currentUser") || "guest";
    const key = `kgraphHistory_${user}`;
    const historyList = document.getElementById("historyList");

    const history = JSON.parse(localStorage.getItem(key) || "[]")
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 10);

    historyList.innerHTML = "";

    history.forEach(entry => {
        const div = document.createElement("div");
        div.className = "history-entry";
        div.innerHTML = `
            <div class="history-filename" title="${entry.filename}"><strong>${entry.filename}</strong></div>
            <div style="font-size: 12px; color: #555;">${new Date(entry.timestamp).toLocaleString()}</div>
        `;
        const filenameDiv = div.querySelector('.history-filename');
        filenameDiv.onclick = (e) => {
            e.stopPropagation(); // Prevent triggering the history entry click
            filenameDiv.classList.toggle('expanded');
        };
        div.onclick = () => loadGraphEntry(entry);
        historyList.appendChild(div);
    });
}

function loadGraphEntry(entry) {
    // Load graph
    drawGraph(entry.graphData);

    // Load triple table
    const tripleTableDiv = document.getElementById("tripleTable");
    const doneBtn = document.getElementById("doneBtn");

    tripleTableDiv.innerHTML =
        `<table><tr><th>Subject</th><th>Predicate</th><th>Object</th></tr>` +
        entry.triples.map((t, i) => `
            <tr>
                <td>${t.subject}</td>
                <td><select data-row="${i}">${predicates.map(p =>
            `<option value="${p}" ${p === t.predicate ? "selected" : ""}>${p}</option>`).join("")}</select></td>
                <td>${t.object}</td>
            </tr>
        `).join("") +
        `</table>`;

    doneBtn.disabled = false;
    filename = entry.filename;
}

function updateHeaderDropdowns() {
    const sFile = document.getElementById("subjectFileSelect").value;
    const oFile = document.getElementById("objectFileSelect").value;
    const subjectSel = document.getElementById("subjectSelect");
    const objectSel = document.getElementById("objectSelect");
    subjectSel.disabled = objectSel.disabled = true;
    subjectSel.innerHTML = objectSel.innerHTML = "";

    (window.uploadedFileInfo || []).forEach(f => {
        if (f.filename === sFile) {
            f.headers.forEach(h => subjectSel.innerHTML += `<option value="${h}">${h}</option>`);
            subjectSel.disabled = false;
        }
        if (f.filename === oFile) {
            f.headers.forEach(h => objectSel.innerHTML += `<option value="${h}">${h}</option>`);
            objectSel.disabled = false;
        }
    });
}

function handleLogin() {
    const username = document.getElementById("usernameInput").value.trim();
    if (!username) {
        alert("Please enter a username.");
        return;
    }

    localStorage.setItem("currentUser", username);
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("mainApp").style.display = "block";
    document.getElementById("currentUserLabel").innerText = `Logged in as: ${username}`;

    populateHistoryList();
}

function logoutUser() {
    // Remove username
    localStorage.removeItem("currentUser");

    // Hide app, show login screen
    document.getElementById("mainApp").style.display = "none";
    document.getElementById("loginScreen").style.display = "flex";

    // Clear file uploads
    selectedFiles = [];
    document.getElementById("selectedFilesList").innerHTML = "";

    // Clear triple table
    document.getElementById("tripleTable").innerHTML = "";

    // Clear dropdowns
    document.getElementById("subjectFileSelect").innerHTML = "";
    document.getElementById("objectFileSelect").innerHTML = "";
    document.getElementById("subjectSelect").innerHTML = "";
    document.getElementById("objectSelect").innerHTML = "";

    document.getElementById("subjectSelect").disabled = true;
    document.getElementById("objectSelect").disabled = true;
    document.getElementById("generateBtn").disabled = true;
    document.getElementById("doneBtn").disabled = true;

    // Clear graph
    const container = document.getElementById("graph");
    container.innerHTML = "";
    document.getElementById("infoBox").innerText = "Click a node or edge to see more details.";

    // Reset file input
    document.getElementById("csvFile").value = "";

    // Clear success and error messages ✅
    document.getElementById("messageBox").style.display = "none";
    document.getElementById("errorBox").style.display = "none";
}

function promptSaveAs() {
    const customName = prompt("Enter a name to save this graph as:");
    if (!customName || customName.trim() === "") return;

    saveToLocalHistory({
        filename: customName.trim(),
        triples: extractTriplesFromTable(),
        graphData: {
            nodes: allNodes,
            edges: allEdges,
            nodeSources: {}  // optional: include if you store this
        }
    });

    alert(`Graph saved as "${customName}"`);
}

function extractTriplesFromTable() {
    const selects = document.querySelectorAll("#tripleTable select");
    const triples = [];
    const subjectFile = document.getElementById("subjectFileSelect").value;
    const objectFile = document.getElementById("objectFileSelect").value;

    selects.forEach(sel => {
        const row = sel.closest("tr");
        triples.push({
            subject: row.children[0].innerText,
            predicate: sel.value,
            object: row.children[2].innerText,
            subjectFile,
            objectFile
        });
    });

    return triples;
}



window.onload = async () => {
    await loadPredicates(); // ✅ load predicates first

    const savedUser = localStorage.getItem("currentUser");
    if (savedUser) {
        document.getElementById("loginScreen").style.display = "none";
        document.getElementById("mainApp").style.display = "block";
        document.getElementById("currentUserLabel").innerText = `Logged in as: ${savedUser}`;
        populateHistoryList();
    }
};
