import React from 'react';
import logo from './logo.svg';


import './App.css';

import Form from 'react-bootstrap/Form';
import Navbar from 'react-bootstrap/Navbar';
import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Button from 'react-bootstrap/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import FormControl from 'react-bootstrap/FormControl';

import { DropletHalf } from 'react-bootstrap-icons';
import { Map, TileLayer, Marker, Popup } from 'react-leaflet';


class Baywatch extends React.Component {
  state = {
    zipCode: "",
    submittedZip: "",
    percentFarmland: 33.3,
    percentForest: 33.3,
    percentUrban: 33.3,
    imageUrl: "",
    metric: "",
    updatedPercentage: false,
    lat: null,
    long: null
  }

  updatePercentage(aDiff, b, c) {
    if((-1*(aDiff / 2)) > b) {
      let remainder = (-1*(aDiff/2)) - b;
      b = 0;
      c = c + (aDiff / 2) - remainder;
    } else if((-1*(aDiff / 2)) > c) {
      let remainder = (-1*(aDiff/2)) - c;
      c = 0;
      b = b + (aDiff / 2) - remainder;
    } else {
      b = b + (aDiff / 2);
      c = c + (aDiff / 2);
    }

    return [b, c];
  }

  setPercent(landType, value) {
    const currentFarmland = parseFloat(this.state.percentFarmland);
    const currentForest = parseFloat(this.state.percentForest);
    const currentUrban = parseFloat(this.state.percentUrban);

    value = parseFloat(value);

    if(landType === "farmland") {
      const farmlandDiff = currentFarmland - value;
      const updatedValues = this.updatePercentage(farmlandDiff, currentForest, currentUrban);
      this.setState({
        updatedPercentage: true,
        percentFarmland: value,
        percentForest: updatedValues[0],
        percentUrban: updatedValues[1]
      });
    } else if(landType === "forest") {
      const forestDiff = currentForest - value;
      const updatedValues = this.updatePercentage(forestDiff, currentFarmland, currentUrban);
      this.setState({
        updatedPercentage: true,
        percentFarmland: updatedValues[0],
        percentForest: value,
        percentUrban: updatedValues[1]
      });
    } else if(landType === "urban") {
      const urbanDiff = currentUrban - value;
      const updatedValues = this.updatePercentage(urbanDiff, currentFarmland, currentForest);
      this.setState({
        updatedPercentage: true,
        percentFarmland: updatedValues[0],
        percentForest: updatedValues[1],
        percentUrban: value
      });
    }
  }

  setMetric(value) {
    this.setState({
      metric: value
    });
  }

  setZipCode(value) {
    this.setState({
      zipCode: value
    })
  }

  updateImageUrl() {
    const zip = this.state.zipCode;
    const metric = this.state.metric;

    let url = "http://localhost:5000/plot.png?zip=" + zip + "&metric=" + metric;

    if(this.state.updatedPercentage && this.state.zipCode === this.state.submittedZip) {
      const farm = this.state.percentFarmland;
      const urban = this.state.percentUrban;
      const forest = this.state.percentForest;

      url = url + "&farm=" + farm + "&urban=" + urban + "&forest=" + forest;
    } else {
      this.fetchPercentages()
    }

    this.setState({
      imageUrl: url,
      submittedZip: this.state.zipCode
    })
  }

  fetchPercentages() {
    const zip = this.state.zipCode;

    fetch('http://localhost:5000/percentages?zip=' + zip)
        .then(response => response.json())
        .then(data => {
          this.setState({
            percentFarmland: parseFloat(data.farm),
            percentUrban: parseFloat(data.urban),
            percentForest: parseFloat(data.forest),
            lat: parseFloat(data.lat),
            long: parseFloat(data.long)
          })
          console.log(data);
        });
  }

  render() {
    let image = "";
    if(this.state.imageUrl) {
      image = (<img src={this.state.imageUrl} height="400px" />);
    }

    return(
      <div>
        <h3>Can you improve the Chesapeake Bay?</h3><br />
        <Form>
        <Form.Row className="align-items-center">
          <Col md={5}>
            <Form.Control
              as="select"
              className="mr-sm-2"
              id="inlineFormCustomSelect"
              custom
              value={this.state.metric}
              onChange={(e) => this.setMetric(e.target.value)}
            >
              <option value="">Choose a Water Quality Indicator</option>
              <option value="nitrogen">Nitrogen Levels</option>
            </Form.Control>
          </Col>
          <Col md={5}>
            <InputGroup>
              <InputGroup.Prepend>
                <InputGroup.Text>Zip Code</InputGroup.Text>
              </InputGroup.Prepend>
              <FormControl value={this.state.zipCode} onChange={(e) => this.setZipCode(e.target.value)} />
            </InputGroup>
          </Col>
          <Col md={2}>
            <Button onClick={() => this.updateImageUrl()} className="submit-button">Update</Button>
          </Col>
          </Form.Row><br />
          <Form.Row>
            <Col>
            <Form.Group controlId="formBasicRange">
              <Form.Label>% Farmland</Form.Label>
              <Form.Control
                value={this.state.percentFarmland}
                onChange={(e) => this.setPercent("farmland", e.target.value)}
                type="range"
                variant="alert" />
            </Form.Group>
            </Col>
            <Col>
            <Form.Group controlId="formBasicRange">
              <Form.Label>% Forest</Form.Label>
              <Form.Control
                value={this.state.percentForest}
                onChange={(e) => this.setPercent("forest", e.target.value)}
                type="range"
                variant="success" />
            </Form.Group>
            </Col>
            <Col>
            <Form.Group controlId="formBasicRange">
              <Form.Label>% Urban Development</Form.Label>
              <Form.Control
                value={this.state.percentUrban}
                onChange={(e) => this.setPercent("urban", e.target.value)}
                type="range"
                variant="primary" />
            </Form.Group>
            </Col>
          </Form.Row>

        </Form>
        <div className="image-holder container">
          <Row>
            <Col>
              <StationMap lat={this.state.lat} long={this.state.long} />
            </Col>
            <Col>
              {image}
            </Col>
          </Row>
        </div>
      </div>
    );
  }
}

class StationMap extends React.Component {
  render() {
    const latitude = this.props.lat;
    const longitude = this.props.long;

    if(latitude && longitude) {
      return (
        <Map center={[latitude, longitude]}
          zoom={13}
          style={{ width: '100%', height: '400px' }}>
          <TileLayer attribution='&copy <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <Marker position={[latitude, longitude]}>
            <Popup>
              A pretty CSS3 popup. <br /> Easily customizable.
            </Popup>
          </Marker>
        </Map>
      )
    } else {
      return ("Please enter a zipcode and water quality metric.")
    }
  }
}


function Logo() {
  return(
    <Navbar className="nav">
      <DropletHalf color="#33b5e5" /><Navbar.Brand href="/">Baywatch</Navbar.Brand>
      <Navbar.Collapse className="justify-content-end">
        <Navbar.Text>
          <a href="/">About</a>
        </Navbar.Text>
      </Navbar.Collapse>
    </Navbar>
  );
}

function Footer() {
  return (
    <div className="text-center">
      <br />
      <hr />
      Built by the <a href="#">SwampMonsters</a> | <a href="#">Github</a>
    </div>
  );
}

function App() {
  return (
    <Container>
      <Row>
        <Col>
          <Logo />
          <br />
        </Col>
      </Row>
      <Row>
        <Col>
          <Baywatch />
        </Col>
      </Row>
      <Row>
        <Col>
          <Footer />
        </Col>
      </Row>
    </Container>
  );
}

export default App;
