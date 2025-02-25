import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore, doc, setDoc } from "firebase/firestore";

const firebaseConfig = {
    apiKey: "AIzaSyCqZWRApBF5Kzna4EbHJQGJveUE9nEjjRo",
    authDomain: "unfake-d8d9c.firebaseapp.com",
    databaseURL: "https://unfake-d8d9c-default-rtdb.firebaseio.com",
    projectId: "unfake-d8d9c",
    storageBucket: "unfake-d8d9c.appspot.com",
    messagingSenderId: "332199381098",
    appId: "1:332199381098:web:5af91e85108de696602213",
    measurementId: "G-G0QHNLNMZG"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Function to save tweet to Firestore
export const saveTweetToFirebase = async (tweetData) => {
    try {
      const docRef = await addDoc(collection(db, 'tweets'), tweetData);
      console.log("Document written with ID: ", docRef.id);
    } catch (e) {
      console.error("Error adding document: ", e);
    }
  };

// export { auth, db };