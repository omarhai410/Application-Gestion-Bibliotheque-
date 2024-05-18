// @ts-ignore
import express, { Request, Response } from 'express';
import mongoose, { ConnectOptions } from 'mongoose';
// @ts-ignore
import bodyParser from 'body-parser';

const app = express();
const PORT = 3000;

// MongoDB connection
mongoose.connect('mongodb://localhost:27017/LIB', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
} as ConnectOptions)
  .then(() => {
    console.log('MongoDB connected successfully');
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error);
  });

// Create a mongoose schema and model
interface User {
  name: string;
  surname: string;
  email: string;
  telephone: string;
  cne: string;
  cin: string;
  occupation: string;
  password: string;
}

const userSchema = new mongoose.Schema<User>({
  name: String,
  surname: String,
  email: String,
  telephone: String,
  cne: String,
  cin: String,
  occupation: String,
  password: String,
});

const UserModel = mongoose.model<User>('User', userSchema);

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Serve HTML file
app.get('/', (req: Request, res: Response) => {
  res.sendFile(__dirname + '/index.html');
});

// Handle form submission
app.post('/signup', async (req: Request, res: Response) => {
  try {
    const userData: User = req.body;

    // Create a new user instance
    const newUser = new UserModel(userData);

    // Save the user to the database
    await newUser.save();

    res.status(201).json({ message: 'User registered successfully!' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
});
