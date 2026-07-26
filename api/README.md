# 仮想環境作成

# 仮想環境に入る


# pipで Django REST frameworkをインストール
```

```
pip install djangorestframework
---

https://note.com/saito_pythonista/n/nb95c54f4c327

https://blog.cloudsmith.co.jp/2023/08/421/#toc4

https://github.com/ryu-0729/ideal-body-weight-api/tree/main

# 設定ディレクトリの作成
プロジェクト全体のディレクトリを作成後、作成したディレクトリで以下コマンドを実行する。
- ポイント：「config(スペース).」とすること　※「(スペース).」がなければconfigディレクトリが2つできてしまい使い勝手が悪くなる
```
django-admin startproject config .
```

configディレクトリ作成後、configディレクトリ内にviews.pyファイルを作成します。目的は、トップページ(index)の処理をするためです。

# アプリディレクトリの作成

- djangoでは全体を設定/統括する設定ディレクトリと機能単位を各アプリディレクトリで管理するのがベストプラクティス

```
python manage.py startapp accounts
python manage.py startapp blogs
python manage.py startapp QA
```

アプリ名は任意ですが、認証機能のアプリは”accounts”にした方がいいです。
理由としてはdjangoのlogin_requiredといったデコレーターを使う際、accountsでなければ機能しないといった問題が発生するからです。

# 