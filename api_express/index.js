const express = require('express');
const app = express();
const port = process.env.PORT || 3001;

const bodyParser = require('body-parser')
app.use(bodyParser.urlencoded({extended: true}))
app.use(bodyParser.json())

// 全てのリクエストに対して前処理
app.use( '/*', function(req, res, next){
  next();
});

app.get('/test', (req, res, next) => {
  res.send({
    message: 'テスト'
  })
})

app.listen(port, () => {
  console.log(`listening on *:${port}`);
})
