(() => {
  const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"})[char]);
  document.querySelectorAll(".qbi2-coverage").forEach(root => {
    const form = root.closest("form");
    const name = form?.querySelector('[name="obraSocial"]');
    const planName = form?.querySelector('[name="plan"]');
    const financierId = form?.querySelector('[name="qbi2_financiador_id"]');
    const planId = form?.querySelector('[name="qbi2_plan_id"]');
    const affiliate = form?.querySelector('[name="afiliado"]');
    const query = root.querySelector(".qbi2-coverage-query");
    const searchButton = root.querySelector(".qbi2-coverage-search");
    const noneToggle = root.querySelector(".qbi2-coverage-none-input");
    const results = root.querySelector(".qbi2-coverage-results");
    const current = root.querySelector(".qbi2-coverage-current");
    const planWrap = root.querySelector(".qbi2-plan-wrap");
    const planSelect = root.querySelector(".qbi2-plan-select");
    let found = [];
    let coverageMode = "covered";

    const isPrivateCoverage = () => {
      const normalized = name?.value.trim().toLocaleLowerCase().replace(/\s+/g," ");
      return !normalized || ["particular","sin cobertura","ninguna","sin obra social"].includes(normalized);
    };
    const setCoverageMode = mode => {
      coverageMode = mode;
      const withoutCoverage = mode === "none";
      const selectingCoverage = mode === "selecting";
      query.disabled = withoutCoverage;
      searchButton.disabled = withoutCoverage;
      if (affiliate) affiliate.disabled = mode !== "covered";
      planSelect.disabled = mode !== "covered";
      for (const field of [name, planName, financierId, planId]) {
        if (field) field.disabled = withoutCoverage;
      }
      noneToggle.checked = withoutCoverage;
      root.classList.toggle("is-no-coverage", withoutCoverage);
      root.classList.toggle("is-selecting-coverage", selectingCoverage);
      for (const button of results.querySelectorAll("button")) button.disabled = withoutCoverage;
    };

    const renderCurrent = () => {
      const coverage = name?.value.trim();
      current.textContent = coverageMode === "none"
        ? (coverage ? `Sin cobertura · ${coverage} queda conservada` : "Sin cobertura")
        : !isPrivateCoverage()
        ? `${coverage}${planName?.value ? ` · ${planName.value}` : ""}${financierId?.value ? "" : " · requiere actualización"}`
        : coverageMode === "selecting" ? "Seleccionar una cobertura" : "Sin cobertura";
    };
    const setPlans = (plans, preferred="") => {
      planSelect.innerHTML = '<option value="">Seleccionar plan</option>' + plans.map(item => `<option value="${esc(item.id)}">${esc(item.nombre || `Plan ${item.id}`)}</option>`).join("");
      planWrap.hidden = !plans.length;
      planSelect.required = Boolean(plans.length);
      planSelect.value = String(preferred || "");
      if (!plans.length) { planId.value=""; planName.value=""; }
    };
    const selectFinancier = item => {
      name.value=item.nombreComercial || "";
      financierId.value=item.idFinanciador ?? "";
      planId.value=""; planName.value="";
      setPlans(Array.isArray(item.planes) ? item.planes : []);
      results.replaceChildren(); query.value=""; setCoverageMode("covered"); renderCurrent();
      if (!planWrap.hidden) planSelect.focus(); else affiliate?.focus();
    };
    const search = async () => {
      if (coverageMode === "none") return;
      const term=query.value.trim();
      results.textContent="Buscando…";
      try {
        const url=new URL(root.dataset.catalogUrl, location.origin); url.searchParams.set("q",term);
        const response=await fetch(url,{credentials:"same-origin",headers:{Accept:"application/json"}});
        const data=await response.json();
        if(!response.ok) throw new Error(data.message || "No se pudo consultar el catálogo QBI2.");
        found=Array.isArray(data.items) ? data.items : [];
        results.innerHTML=found.length ? found.map((item,index) => `<button type="button" data-index="${index}"><strong>${esc(item.nombreComercial)}</strong><small>${item.planes?.length ? `${item.planes.length} planes` : "Sin planes informados"}</small></button>`).join("") : "No se encontraron coberturas.";
      } catch(error) { results.textContent=error.message; }
    };
    searchButton.addEventListener("click",search);
    query.addEventListener("keydown",event => { if(event.key==="Enter"){event.preventDefault();search();} });
    results.addEventListener("click",event => { const button=event.target.closest("button[data-index]"); if(button) selectFinancier(found[Number(button.dataset.index)]); });
    noneToggle.addEventListener("change",() => {
      if(noneToggle.checked) {
        setCoverageMode("none"); renderCurrent();
        return;
      }
      const restoredCanonicalCoverage = Boolean(name.value.trim() && financierId.value);
      setCoverageMode(restoredCanonicalCoverage ? "covered" : "selecting"); renderCurrent();
      if(restoredCanonicalCoverage) affiliate?.focus(); else query.focus();
    });
    planSelect.addEventListener("change",() => {
      const option=planSelect.selectedOptions[0]; planId.value=option?.value || "";
      planName.value=option?.value ? option.textContent.trim() : ""; renderCurrent();
    });
    setCoverageMode(isPrivateCoverage() ? "none" : "covered");
    renderCurrent();
    if(financierId?.value){
      const url=new URL(root.dataset.catalogUrl,location.origin); url.searchParams.set("id",financierId.value);
      fetch(url,{credentials:"same-origin",headers:{Accept:"application/json"}}).then(response=>response.json()).then(data=>{
        const item=data.items?.[0]; if(item) setPlans(item.planes || [],planId.value);
      }).catch(()=>{});
    }
  });
})();
