const meiliService = {
  send(method, url, body) {
    $http.send({
      url: `${this.meiliUrl}${url}`,
      method,
      body: JSON.stringify(body),
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.meiliMasterKey}`,
      },
    });
  },
  init() {
    console.log("Initializing Meilisearch");
    this.meiliUrl = $os.getenv("MEILI_URL");
    this.meiliMasterKey = $os.getenv("MEILI_MASTER_KEY");
    this.openaiApiKey = $os.getenv("OPENAI_API_KEY");

    this.embedders = {
      "materialChunks-openai": {
        source: "openAi",
        model: "text-embedding-3-small",
        apiKey: this.openaiApiKey,
        documentTemplate: "Chunk {{doc.title}}: {{doc.content}}",
      },
      "quizChunks-openai": {
        source: "openAi",
        model: "text-embedding-3-small",
        apiKey: this.openaiApiKey,
        documentTemplate: "Chunk {{doc.title}}: {{doc.content}}",
      },
    };

    // Material Chunks
    this.send("PATCH", "indexes/materialChunks/settings/embedders", {
      embedders: this.embedders.materialChunks,
    });
    this.send("PUT", "indexes/materialChunks/settings/filterable-attributes", [
      "userId",
      "materialId",
    ]);

    // Quiz Chunks
    this.send("PATCH", "indexes/quizChunks/settings/embedders", {
      embedders: this.embedders.quizChunks,
    });
    this.send("PUT", "indexes/quizChunks/settings/filterable-attributes", [
      "userId",
      "quizId",
    ]);

    console.log("Meilisearch initialized");
  },

  
  // upsert: (documents, index) => {
  //   const res = $http.send({
  //     url: `${this.meiliUrl}indexes/${index}/documents`,
  //     method: "POST",
  //     body: JSON.stringify(documents),
  //   });
  //   return res;
  // },
  // deleteByFilter: (filter, index) => {
  //   const res = $http.send({
  //     url: `${this.meiliUrl}indexes/${index}/documents/delete`,
  //     method: "POST",
  //     body: JSON.stringify({
  //       // filter: `documentId = "${documentId}"`,
  //       filter,
  //     }),
  //     headers: {
  //       "Content-Type": "application/json",
  //       Authorization: `Bearer ${this.meiliMasterKey}`,
  //     },
  //   });
  //   return res;
  // },
};

module.exports = {
  meiliService,
};
