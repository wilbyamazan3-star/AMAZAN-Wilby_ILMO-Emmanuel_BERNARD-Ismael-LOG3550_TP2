// Adresse de l'API FastAPI (devoir 2). Elle doit tourner en local : uvicorn app.main:app --reload
const API_URL = "http://127.0.0.1:8000";
const PAGE_SIZE = 100; // limite maximale acceptée par GET /livres

const currentYear = new Date().getFullYear();
let books = [];
let loadFailed = false;

const bookList = document.querySelector("#book-list");
const searchInput = document.querySelector("#search");
const categoryFilter = document.querySelector("#category-filter");
const availableOnly = document.querySelector("#available-only");
const sortSelect = document.querySelector("#sort");
const resultCount = document.querySelector("#result-count");
const emptyMessage = document.querySelector("#empty-message");
const loadingMessage = document.querySelector("#loading-message");
const errorBanner = document.querySelector("#error-banner");
const errorText = document.querySelector("#error-text");
const form = document.querySelector("#book-form");
const formStatus = document.querySelector("#form-status");
const submitButton = form.querySelector("button[type='submit']");

/* ---------- Communication avec l'API ---------- */

// Transforme une réponse d'erreur de l'API en message lisible.
async function readErrorMessage(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail; // 404, 409
    if (Array.isArray(body.detail)) {                        // 422 : liste d'erreurs
      return body.detail
        .map(err => `${err.loc[err.loc.length - 1]} : ${err.msg}`)
        .join(" ; ");
    }
  } catch (error) {
    // La réponse n'est pas du JSON : on retombe sur le message générique.
  }
  return `Erreur du serveur (code ${response.status}).`;
}

// Appelle l'API ; lève une Error avec un message clair en cas d'échec.
async function apiFetch(path, options = {}) {
  let response;
  try {
    response = await fetch(API_URL + path, options);
  } catch (error) {
    // fetch échoue (TypeError) quand le serveur est arrêté ou injoignable.
    throw new Error("Impossible de joindre l'API. Vérifiez que le serveur est démarré.");
  }
  if (!response.ok) throw new Error(await readErrorMessage(response));
  return response.status === 204 ? null : response.json();
}

/* ---------- Chargement ---------- */

function setLoading(isLoading) {
  loadingMessage.hidden = !isLoading;
  if (isLoading) {
    errorBanner.hidden = true;
    emptyMessage.hidden = true;
  }
}

async function loadBooks() {
  setLoading(true);
  loadFailed = false;
  try {
    const all = [];
    let skip = 0;
    while (true) {
      const page = await apiFetch(`/livres?skip=${skip}&limit=${PAGE_SIZE}`);
      all.push(...page);
      if (page.length < PAGE_SIZE) break;
      skip += PAGE_SIZE;
    }
    books = all;
  } catch (error) {
    loadFailed = true;
    books = [];
    errorText.textContent = error.message;
    errorBanner.hidden = false;
  } finally {
    loadingMessage.hidden = true;
    renderBooks();
  }
}

/* ---------- Affichage (filtres et tri faits dans le navigateur) ---------- */

function normalizeText(value) {
  return value.toLocaleLowerCase("fr").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function getVisibleBooks() {
  const query = normalizeText(searchInput.value.trim());
  const category = categoryFilter.value;

  const filtered = books.filter(book => {
    const matchesText = normalizeText(book.titre + " " + book.auteur).includes(query);
    const matchesCategory = category === "toutes" || book.categorie === category;
    const matchesAvailability = !availableOnly.checked || book.disponible;
    return matchesText && matchesCategory && matchesAvailability;
  });

  const [sortKey, direction] = sortSelect.value.split("-");
  return filtered.sort((a, b) => {
    const comparison = sortKey === "titre"
      ? a.titre.localeCompare(b.titre, "fr", { sensitivity: "base" })
      : a.annee - b.annee;
    return direction === "asc" ? comparison : -comparison;
  });
}

function createBookCard(book) {
  const article = document.createElement("article");
  article.className = "book-card";

  const title = document.createElement("h3");
  title.textContent = book.titre;

  const author = document.createElement("p");
  author.className = "book-author";
  author.textContent = "Auteur : " + book.auteur;

  const year = document.createElement("p");
  year.className = "book-year";
  year.textContent = "Année : " + book.annee;

  const category = document.createElement("span");
  category.className = "category";
  category.textContent = book.categorie;

  const status = document.createElement("span");
  status.className = "status " + (book.disponible ? "available" : "borrowed");
  status.textContent = book.disponible ? "Disponible" : "Emprunté";

  const actions = document.createElement("div");
  actions.className = "card-actions";
  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "button delete-button";
  deleteButton.textContent = "Supprimer";
  deleteButton.setAttribute("aria-label", "Supprimer le livre " + book.titre);
  deleteButton.addEventListener("click", () => deleteBook(book.id, deleteButton));
  actions.append(deleteButton);

  article.append(title, author, year, category, status, actions);
  return article;
}

function renderBooks() {
  const visibleBooks = getVisibleBooks();
  bookList.replaceChildren(...visibleBooks.map(createBookCard));
  resultCount.textContent = loadFailed
    ? ""
    : visibleBooks.length + (visibleBooks.length > 1 ? " résultats" : " résultat");
  // Si l'API est en panne, on affiche l'erreur et non « aucun livre ».
  emptyMessage.hidden = loadFailed || !loadingMessage.hidden || visibleBooks.length !== 0;
}

function setStatus(message, isError = false) {
  formStatus.textContent = message;
  formStatus.classList.toggle("is-error", isError);
}

/* ---------- Suppression ---------- */

async function deleteBook(id, button) {
  const book = books.find(item => item.id === id);
  if (!book || !window.confirm(`Voulez-vous vraiment supprimer « ${book.titre} » ?`)) return;

  button.disabled = true;
  try {
    await apiFetch(`/livres/${id}`, { method: "DELETE" });
    books = books.filter(item => item.id !== id);
    renderBooks();
    setStatus("Le livre a été supprimé.");
  } catch (error) {
    button.disabled = false;
    setStatus("Suppression impossible : " + error.message, true);
  }
}

/* ---------- Formulaire d'ajout ---------- */

function showError(field, message) {
  document.querySelector("#" + field + "-error").textContent = message;
  document.querySelector("#" + field).setAttribute("aria-invalid", message ? "true" : "false");
}

function validateForm(values) {
  let valid = true;
  const title = values.title.trim();
  const author = values.author.trim();
  const year = Number(values.year);
  const isbn = values.isbn.trim();

  const checks = {
    title: title.length >= 2 ? "" : "Le titre doit contenir au moins 2 caractères.",
    author: author.length >= 2 ? "" : "L'auteur doit contenir au moins 2 caractères.",
    year: Number.isInteger(year) && year >= 1450 && year <= currentYear
      ? "" : `L'année doit être comprise entre 1450 et ${currentYear}.`,
    category: ["roman", "science", "histoire", "informatique", "autre"].includes(values.category)
      ? "" : "Veuillez choisir une catégorie.",
    isbn: isbn === "" || /^(\d{10}|\d{13})$/.test(isbn)
      ? "" : "L'ISBN doit contenir 10 ou 13 chiffres, sans tirets."
  };

  Object.entries(checks).forEach(([field, message]) => {
    showError(field, message);
    if (message) valid = false;
  });
  return valid;
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  setStatus("");
  const values = {
    title: form.elements.title.value,
    author: form.elements.author.value,
    year: form.elements.year.value,
    category: form.elements.category.value,
    isbn: form.elements.isbn.value
  };
  if (!validateForm(values)) {
    setStatus("Veuillez corriger les champs indiqués.", true);
    return;
  }

  const newBook = {
    titre: values.title.trim(),
    auteur: values.author.trim(),
    annee: Number(values.year),
    categorie: values.category,
    disponible: true
  };
  if (values.isbn.trim() !== "") newBook.isbn = values.isbn.trim();

  submitButton.disabled = true;
  setStatus("Envoi en cours…");
  try {
    const created = await apiFetch("/livres", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newBook)
    });
    books.push(created); // l'API renvoie le livre avec son id généré
    form.reset();
    ["title", "author", "year", "category", "isbn"].forEach(field => showError(field, ""));
    renderBooks();
    setStatus("Le livre a été ajouté avec succès.");
  } catch (error) {
    setStatus("Ajout impossible : " + error.message, true);
  } finally {
    submitButton.disabled = false;
  }
});

[searchInput, categoryFilter, availableOnly, sortSelect].forEach(control => {
  control.addEventListener("input", renderBooks);
  control.addEventListener("change", renderBooks);
});

document.querySelector("#retry-button").addEventListener("click", loadBooks);

document.querySelector("#year").max = String(currentYear);
loadBooks();
