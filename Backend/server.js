const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const cors = require('cors');
const app = express();
const PORT = 3030;

// Middlewaret
app.use(cors());
app.use(bodyParser.json());

// Luo kansio raporteille, jos ei ole olemassa
const reportsDir = './reports';
if (!fs.existsSync(reportsDir)) {
  fs.mkdirSync(reportsDir);
}

// POST: vastaanota agentin raportti
app.post('/report', (req, res) => {
  const report = req.body;
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const filename = `${reportsDir}/report-${timestamp}.json`;

  fs.writeFile(filename, JSON.stringify(report, null, 2), (err) => {
    if (err) {
      console.error('Virhe tallennuksessa:', err);
      return res.status(500).send('Tallennus epäonnistui');
    }
    console.log('Raportti tallennettu:', filename);
    res.status(200).send('OK');
  });
});

// GET: tarkastelusivu (tulevaisuudessa dashboard)
app.get('/', (req, res) => {
  res.send('<h1>NIS2 Backend toimii ✅</h1><p>Lähetä raportti endpointtiin <code>/report</code></p>');
});

app.listen(PORT, () => {
  console.log(`Palvelin käynnissä http://localhost:${PORT}`);
});
