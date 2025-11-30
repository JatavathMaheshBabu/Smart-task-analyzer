// frontend/script.js
const taskForm = document.getElementById("taskForm");
const addBtn = document.getElementById("addBtn");
const clearListBtn = document.getElementById("clearListBtn");
const jsonInput = document.getElementById("jsonInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const strategyEl = document.getElementById("strategy");
const resultsEl = document.getElementById("results");
const summaryEl = document.getElementById("summary");
const inputError = document.getElementById("inputError");
const noResults = document.getElementById("noResults");

let taskList = []; 

function showError(msg){
  inputError.hidden = false;
  inputError.textContent = msg;
}
function clearError(){
  inputError.hidden = true;
  inputError.textContent = "";
}
function setSummary(){
  if(taskList.length === 0) summaryEl.textContent = "No tasks in list";
  else summaryEl.textContent = `${taskList.length} task(s) ready to analyze`;
}

// parse dependencies text -> array
function parseDeps(text){
  if(!text) return [];
  return text.split(",").map(s=>s.trim()).filter(Boolean);
}

taskForm.addEventListener("submit", (e) => {
  e.preventDefault();
  clearError();
  const id = document.getElementById("task_id").value.trim();
  const title = document.getElementById("task_title").value.trim();
  const due = document.getElementById("task_due").value.trim();
  const hours = document.getElementById("task_hours").value.trim();
  const importance = document.getElementById("task_importance").value.trim();
  const deps = parseDeps(document.getElementById("task_deps").value);

  if(!title){
    showError("Title is required for a single task.");
    return;
  }

  const obj = {
    id: id || undefined,
    title,
    due_date: due || null,
    estimated_hours: hours ? Number(hours) : null,
    importance: importance ? Number(importance) : null,
    dependencies: deps
  };
  taskList.push(obj);
  document.getElementById("task_title").value = "";
  document.getElementById("task_due").value = "";
  document.getElementById("task_hours").value = "";
  document.getElementById("task_importance").value = "";
  document.getElementById("task_deps").value = "";
  renderTasksPreview();
  setSummary();
});

clearListBtn.addEventListener("click", () => {
  taskList = [];
  renderTasksPreview();
  setSummary();
  clearError();
});

// render a small preview of the tasks 
function renderTasksPreview(){
  if(taskList.length === 0){
    resultsEl.innerHTML = "";
    noResults.hidden = false;
    return;
  }
  noResults.hidden = true;
  resultsEl.innerHTML = "";
  taskList.forEach(t => {
    const li = document.createElement("li");
    li.className = "result-item";
    li.innerHTML = `
      <div class="result-main">
        <div class="title-row"><h3>${escapeHtml(t.title)}</h3></div>
        <div class="meta small muted">Due: ${t.due_date || "—"} • Est: ${t.estimated_hours ?? "—"}h • Importance: ${t.importance ?? "—"}</div>
      </div>
      <div style="min-width:80px;text-align:center">
        <div class="badge muted">—</div>
      </div>
    `;
    resultsEl.appendChild(li);
  });
}

function escapeHtml(s){
  if(s == null) return "";
  return String(s).replace(/[&<>"']/g, c=>({ '&': '&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
}

// client-side sorts
function frontendSort(tasks, mode){
  if(mode === "fastest"){
    return tasks.slice().sort((a,b) => ( (a.estimated_hours ?? 9999) - (b.estimated_hours ?? 9999) ));
  } else if(mode === "impact"){
    return tasks.slice().sort((a,b) => ( (b.importance ?? 0) - (a.importance ?? 0) ));
  } else if(mode === "deadline"){
    const dA = a => a.due_date || "9999-12-31";
    return tasks.slice().sort((a,b) => dA(a).localeCompare(dA(b)));
  }
  return tasks;
}

function scoreToClass(score){
  if(score >= 7.5) return "priority-high";
  if(score >= 4.5) return "priority-med";
  return "priority-low";
}

function renderResults(list){
  resultsEl.innerHTML = "";
  if(!list || list.length === 0){
    noResults.hidden = false;
    return;
  }
  noResults.hidden = true;
  list.forEach(t => {
    const li = document.createElement("li");
    li.className = "result-item";
    const cls = scoreToClass(t.score);
    li.innerHTML = `
      <div class="result-main">
        <div class="title-row">
          <h3>${escapeHtml(t.title)}</h3>
          <div class="small muted">id: ${escapeHtml(t.id ?? "—")}</div>
        </div>
        <div class="expl">${escapeHtml(t.explanation ? formatExplanation(t.explanation) : "")}</div>
        <div class="meta">Due: ${t.due_date || "—"} • Est: ${t.estimated_hours ?? "—"}h • Importance: ${t.importance ?? "—"}</div>
      </div>
      <div>
        <div class="badge ${cls}">${t.score}</div>
      </div>
    `;
    resultsEl.appendChild(li);
  });
}

function formatExplanation(expl){
  if(!expl) return "";
  return `urgency=${expl.urgency}, importance=${expl.importance}, effort=${expl.effort}, dependency=${expl.dependency}`;
}

analyzeBtn.addEventListener("click", async () => {
  clearError();
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analyzing…";

  let tasks = [];
  if(taskList.length) tasks = tasks.concat(taskList);

  const raw = jsonInput.value.trim();
  if(raw){
    try {
      const parsed = JSON.parse(raw);
      if(!Array.isArray(parsed)) throw new Error("JSON must be an array of tasks");
      tasks = tasks.concat(parsed);
    } catch(e){
      showError("Invalid JSON: " + e.message);
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "Analyze Tasks";
      return;
    }
  }

  if(tasks.length === 0){
    showError("No tasks provided. Add a task or paste a JSON array.");
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze Tasks";
    return;
  }

  try {
    const resp = await fetch("/api/tasks/analyze/", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({tasks})
    });

    const data = await resp.json();
    if(!resp.ok){
      if(data.errors) showError(JSON.stringify(data.errors));
      else if(data.error) showError(data.error);
      else showError("Server error");
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "Analyze Tasks";
      return;
    }

    let list = data.sorted || data.tasks || [];
    const strat = strategyEl.value;
    if(strat !== "smart"){
      list = frontendSort(list, strat);
    }

    renderResults(list);
    summaryEl.textContent = `Showing ${list.length} task(s). Strategy: ${strategyEl.options[strategyEl.selectedIndex].text}`;
  } catch(err){
    showError("Network error: " + err.message);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze Tasks";
  }
});

// initial UI state
setSummary();
renderTasksPreview();
