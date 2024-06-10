import { Router, Switch, Route } from 'wouter'

import { HomePage } from './routes/home'
import { WebRTCPage } from './routes/webrtc'
import { SignInPage } from './routes/signin'
import { SignUpPage } from './routes/signup'

function App() {
  return (
    <Router base="/app">
      <Switch>
        <Route path="/" component={HomePage} />
        <Route path="/webrtc" component={WebRTCPage} />
        <Route path="/signin" component={SignInPage} />
        <Route path="/signup" component={SignUpPage} />
        <Route>404</Route>
      </Switch>
    </Router>
  )
}

export default App
