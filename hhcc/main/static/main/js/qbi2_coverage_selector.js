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
    const results = root.querySelector(".qbi2-coverage-results");
    const current = root.querySelector(".qbi2-coverage-current");
    const planWrap = root.querySelector(".qbi2-plan-wrap");
    const planSelect = root.querySelector(".qbi2-plan-select");
    let found = [];

    const renderCurrent = () => {
      const coverage = name?.value.trim();
      const normalized = coverage?.toLocaleLowerCase().replace(/\s+/g," ");
      const isPrivate = !coverage || ["particular","sin cobertura","ninguna","sin obra social"].includes(normalized);
      current.textContent = !isPrivate
        ? `${coverage}${planName?.value ? ` · ${planName.value}` : ""}${financierId?.value ? "" : " · requiere actualización"}`
        : "Sin cobertura";
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
      results.replaceChildren(); query.value=""; renderCurrent();
      if (!planWrap.hidden) planSelect.focus();
    };
    const search = async () => {
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
    root.querySelector(".qbi2-coverage-search").addEventListener("click",search);
    query.addEventListener("keydown",event => { if(event.key==="Enter"){event.preventDefault();search();} });
    results.addEventListener("click",event => { const button=event.target.closest("button[data-index]"); if(button) selectFinancier(found[Number(button.dataset.index)]); });
    root.querySelector(".qbi2-coverage-none").addEventListener("click",() => {
      name.value=""; planName.value=""; financierId.value=""; planId.value="";
      if(affiliate) affiliate.value="";
      setPlans([]); results.replaceChildren(); query.value=""; renderCurrent();
    });
    planSelect.addEventListener("change",() => {
      const option=planSelect.selectedOptions[0]; planId.value=option?.value || "";
      planName.value=option?.value ? option.textContent.trim() : ""; renderCurrent();
    });
    renderCurrent();
    if(financierId?.value){
      const url=new URL(root.dataset.catalogUrl,location.origin); url.searchParams.set("id",financierId.value);
      fetch(url,{credentials:"same-origin",headers:{Accept:"application/json"}}).then(response=>response.json()).then(data=>{
        const item=data.items?.[0]; if(item) setPlans(item.planes || [],planId.value);
      }).catch(()=>{});
    }
  });
})();
