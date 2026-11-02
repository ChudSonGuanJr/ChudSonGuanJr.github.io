(() => {
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Hero slideshow
  const slides = [...document.querySelectorAll(".slide")];
  if (slides.length > 1 && !reducedMotion) {
    let current = 0;
    setInterval(() => {
      if (document.hidden) return;
      slides[current].classList.remove("is-active");
      current = (current + 1) % slides.length;
      slides[current].classList.add("is-active");
    }, 6000);
  }

  // Solid masthead once the page moves off the top
  const masthead = document.querySelector(".masthead");
  const updateMasthead = () => masthead.classList.toggle("is-scrolled", scrollY > 40);
  addEventListener("scroll", updateMasthead, { passive: true });
  updateMasthead();

  // Before and after sliders
  document.querySelectorAll(".img-compare").forEach((el) => {
    const top = el.querySelector(".compare-top");
    const input = el.querySelector("input");
    const divider = el.querySelector(".divider");
    const update = () => {
      top.style.clipPath = `inset(0 ${100 - input.value}% 0 0)`;
      divider.style.left = `${input.value}%`;
    };
    input.addEventListener("input", update);
    update();
  });

  // Left and right arrow keys move between sections
  addEventListener("keydown", (event) => {
    if (document.querySelector("dialog[open]") || event.altKey || event.ctrlKey || event.metaKey) return;
    if (event.key === "ArrowLeft") document.querySelector("[data-section-prev]")?.click();
    if (event.key === "ArrowRight") document.querySelector("[data-section-next]")?.click();
  });

  // Lightbox
  const links = [...document.querySelectorAll("[data-lightbox]")];
  if (!links.length) return;

  const box = document.createElement("dialog");
  box.className = "lightbox";
  box.setAttribute("aria-label", "Image viewer");
  box.innerHTML = `
    <img alt="">
    <button type="button" class="lb-close" aria-label="Close">×</button>
    <button type="button" class="lb-prev" aria-label="Previous image">‹</button>
    <button type="button" class="lb-next" aria-label="Next image">›</button>`;
  document.body.append(box);

  const image = box.querySelector("img");
  let index = 0;
  let shown = links;

  const show = (i) => {
    index = (i + shown.length) % shown.length;
    image.src = shown[index].href;
    image.alt = shown[index].dataset.alt || shown[index].querySelector("img").alt;
    // Keeps the page behind the viewer on the image being shown.
    shown[index].scrollIntoView({ block: "center", behavior: reducedMotion ? "auto" : "smooth" });
  };

  links.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      // Phones and desktops show different versions of split sheets, so skip the hidden ones.
      shown = links.filter((item) => item.offsetParent);
      show(shown.indexOf(link));
      box.showModal();
    });
  });

  box.querySelector(".lb-close").addEventListener("click", () => box.close());
  box.querySelector(".lb-prev").addEventListener("click", () => show(index - 1));
  box.querySelector(".lb-next").addEventListener("click", () => show(index + 1));
  box.addEventListener("click", (event) => {
    if (event.target === box) box.close();
  });
  box.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") show(index - 1);
    if (event.key === "ArrowRight") show(index + 1);
  });
})();
