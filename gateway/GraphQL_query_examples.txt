#1
{
  transaction(id: "PwuNAVJ2fvo44qj9FJLKwmm79baRykHRb7UkQMCFqA8") {
    tags {
      name
      value
    }
    timestamp
    height
    title: tagValue(tagName:"page:title")
    contentType: tagValue(tagName:"Content-Type")
  }
}


#2
{
  transaction(id: "2dS5_bp4_Qj1YHkIIaOPRWr4nmV2G8PR_20UVhMppeg") {
    id
    tags {
      name
      value
    }
    linkedFromTransactions(byForeignTag: "Question-Tx", tags: [{name: "App-Name", value: "querweave"}], from: "C8g_NDQlKt1T_QxxmDnXZWDogV3Iu84YbDc6lAs06a0", to: "") {
      id
      tags {
        name
        value
      }
      linkedToTransaction(byOwnTag: "Question-Tx") {
        id
      }
    }
    countLinkedFromTransactions(byForeignTag: "Question-Tx", tags: [{name: "App-Name", value: "querweave"}], from: "C8g_NDQlKt1T_QxxmDnXZWDogV3Iu84YbDc6lAs06a0", to: "")
  }
}


#3
{
  countTransactions(from: "C8g_NDQlKt1T_QxxmDnXZWDogV3Iu84YbDc6lAs06a0", tags: [{name: "App-Name", value: "querweave"}])
}


#4
{
  transactions(tags: [{name: "App-Name", value: "querweave"}, {name: "Type", value: "question"}]) {
    id
    answers: linkedFromTransactions(byForeignTag: "Question-Tx", tags: [{name: "App-Name", value: "querweave"}, {name: "Type", value: "answer"}]) {
      id
    }
  }
}


#5
{
  transaction(id: "k58YkU0YUCWBy3sklZgF3gdF06z-lFyk_mt-NuyBob0") {
    id
    tags {
      name
      value
    }
    linkedToTransaction(byOwnTag: "Question-Tx") {
      id
      tags {
        name
        value
      }
    }
  }
}
