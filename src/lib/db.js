import fetch from 'node-fetch'

let user_set_words = {}
const response_usw = await fetch('http://localhost:3300/json/user_set_word_ids.json')
if (response_usw.ok) {
    user_set_words = await response_usw.json();
} else {
    console.log("User set word ids file not yet created")
}

const admin={
    "user_set_words":user_set_words,
}

export default admin;
